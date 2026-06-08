from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import json
import mimetypes
from datetime import datetime, timedelta

from .models_suporte import (
    Ticket, CategoriaTicket, InteracaoTicket, AnexoTicket, 
    BaseConhecimento, ConfiguracaoSuporte, EscalacaoTicket
)
from .models_perfil import PerfilUsuario, verificar_permissao


@login_required
def dashboard_suporte(request):
    """Dashboard principal do sistema de suporte"""
    
    # Verificar permissão
    if not verificar_permissao(request.user, 'suporte', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar o sistema de suporte.')
        return redirect('core:dashboard')
    
    # Estatísticas gerais
    total_tickets = Ticket.objects.count()
    tickets_abertos = Ticket.objects.filter(status__in=['aberto', 'em_andamento']).count()
    tickets_aguardando = Ticket.objects.filter(status='aguardando_cliente').count()
    tickets_resolvidos_hoje = Ticket.objects.filter(
        resolvido_em__date=timezone.now().date()
    ).count()
    
    # Tickets por prioridade
    tickets_por_prioridade = Ticket.objects.filter(
        status__in=['aberto', 'em_andamento']
    ).values('prioridade').annotate(total=Count('id'))
    
    # Tickets por categoria
    tickets_por_categoria = Ticket.objects.filter(
        status__in=['aberto', 'em_andamento']
    ).values('categoria__nome').annotate(total=Count('id'))[:5]
    
    # SLA
    tickets_sla_violado = Ticket.objects.filter(
        Q(sla_primeira_resposta_cumprido=False) | Q(sla_resolucao_cumprido=False)
    ).count()
    
    # Meus tickets (se for responsável)
    meus_tickets = Ticket.objects.filter(
        responsavel=request.user,
        status__in=['aberto', 'em_andamento']
    ).order_by('-criado_em')[:5]
    
    # Tickets recentes
    tickets_recentes = Ticket.objects.all().order_by('-criado_em')[:10]
    
    # Avaliação média
    avaliacao_media = Ticket.objects.filter(
        avaliacao_atendimento__isnull=False
    ).aggregate(media=Avg('avaliacao_atendimento'))['media'] or 0
    
    context = {
        'total_tickets': total_tickets,
        'tickets_abertos': tickets_abertos,
        'tickets_aguardando': tickets_aguardando,
        'tickets_resolvidos_hoje': tickets_resolvidos_hoje,
        'tickets_por_prioridade': tickets_por_prioridade,
        'tickets_por_categoria': tickets_por_categoria,
        'tickets_sla_violado': tickets_sla_violado,
        'meus_tickets': meus_tickets,
        'tickets_recentes': tickets_recentes,
        'avaliacao_media': round(avaliacao_media, 1),
    }
    
    return render(request, 'core/suporte/dashboard.html', context)


@login_required
def listar_tickets(request):
    """Lista todos os tickets com filtros"""
    
    # Verificar permissão
    if not verificar_permissao(request.user, 'suporte', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar os tickets.')
        return redirect('core:dashboard')
    
    # Filtros
    tickets = Ticket.objects.all()
    
    # Filtro por status
    status_filtro = request.GET.get('status')
    if status_filtro:
        tickets = tickets.filter(status=status_filtro)
    
    # Filtro por prioridade
    prioridade_filtro = request.GET.get('prioridade')
    if prioridade_filtro:
        tickets = tickets.filter(prioridade=prioridade_filtro)
    
    # Filtro por categoria
    categoria_filtro = request.GET.get('categoria')
    if categoria_filtro:
        tickets = tickets.filter(categoria_id=categoria_filtro)
    
    # Filtro por responsável
    responsavel_filtro = request.GET.get('responsavel')
    if responsavel_filtro:
        if responsavel_filtro == 'meus':
            tickets = tickets.filter(responsavel=request.user)
        else:
            tickets = tickets.filter(responsavel_id=responsavel_filtro)
    
    # Filtro por solicitante
    solicitante_filtro = request.GET.get('solicitante')
    if solicitante_filtro:
        tickets = tickets.filter(solicitante_id=solicitante_filtro)
    
    # Busca por texto
    busca = request.GET.get('busca')
    if busca:
        tickets = tickets.filter(
            Q(numero__icontains=busca) |
            Q(titulo__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(tags__icontains=busca)
        )
    
    # Ordenação
    ordenacao = request.GET.get('ordenacao', '-criado_em')
    tickets = tickets.order_by(ordenacao)
    
    # Paginação
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    categorias = CategoriaTicket.objects.filter(ativo=True)
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'status_choices': Ticket.STATUS_CHOICES,
        'prioridade_choices': Ticket.PRIORIDADES,
        'filtros_ativos': {
            'status': status_filtro,
            'prioridade': prioridade_filtro,
            'categoria': categoria_filtro,
            'responsavel': responsavel_filtro,
            'solicitante': solicitante_filtro,
            'busca': busca,
            'ordenacao': ordenacao,
        }
    }
    
    return render(request, 'core/suporte/listar_tickets.html', context)


@login_required
def criar_ticket(request):
    """Cria um novo ticket"""
    
    if request.method == 'POST':
        try:
            # Dados do formulário
            titulo = request.POST.get('titulo')
            descricao = request.POST.get('descricao')
            categoria_id = request.POST.get('categoria')
            prioridade = request.POST.get('prioridade', 'normal')
            canal = request.POST.get('canal', 'web')
            
            # Relacionamentos opcionais
            proprietario_id = request.POST.get('proprietario')
            inquilino_id = request.POST.get('inquilino')
            
            # Validações
            if not titulo or not descricao or not categoria_id:
                messages.error(request, 'Título, descrição e categoria são obrigatórios.')
                return redirect('suporte:criar_ticket')
            
            categoria = get_object_or_404(CategoriaTicket, id=categoria_id)
            
            # Criar ticket
            ticket = Ticket.objects.create(
                titulo=titulo,
                descricao=descricao,
                categoria=categoria,
                prioridade=prioridade,
                canal=canal,
                solicitante=request.user
            )
            
            # Relacionamentos opcionais
            if proprietario_id:
                from .models import Proprietario
                ticket.proprietario = get_object_or_404(Proprietario, id=proprietario_id)
            
            if inquilino_id:
                from .models import Inquilino
                ticket.inquilino = get_object_or_404(Inquilino, id=inquilino_id)
            
            ticket.save()
            
            # Processar anexos
            anexos = request.FILES.getlist('anexos')
            for anexo in anexos:
                AnexoTicket.objects.create(
                    ticket=ticket,
                    arquivo=anexo,
                    usuario=request.user
                )
            
            messages.success(request, f'Ticket #{ticket.numero} criado com sucesso!')
            return redirect('detalhes_ticket', ticket_id=ticket.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao criar ticket: {str(e)}')
    
    # Dados para o formulário
    categorias = CategoriaTicket.objects.filter(ativo=True)
    
    context = {
        'categorias': categorias,
        'prioridade_choices': Ticket.PRIORIDADES,
        'canal_choices': Ticket.CANAIS,
    }
    
    return render(request, 'core/suporte/criar_ticket.html', context)


@login_required
def detalhes_ticket(request, ticket_id):
    """Exibe detalhes de um ticket"""
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Verificar permissão
    if not ticket.pode_visualizar(request.user):
        messages.error(request, 'Você não tem permissão para visualizar este ticket.')
        return redirect('suporte:listar_tickets')
    
    # Interações do ticket
    interacoes = ticket.interacoes.all().order_by('criado_em')
    
    # Anexos do ticket
    anexos = ticket.anexos.all().order_by('criado_em')
    
    # Escalações
    escalacoes = ticket.escalacoes.all().order_by('-criado_em')
    
    context = {
        'ticket': ticket,
        'interacoes': interacoes,
        'anexos': anexos,
        'escalacoes': escalacoes,
        'pode_editar': ticket.pode_editar(request.user),
        'status_choices': Ticket.STATUS_CHOICES,
        'prioridade_choices': Ticket.PRIORIDADES,
    }
    
    return render(request, 'core/suporte/detalhes_ticket.html', context)


@login_required
@require_http_methods(["POST"])
def responder_ticket(request, ticket_id):
    """Adiciona uma resposta ao ticket"""
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Verificar permissão
    if not ticket.pode_visualizar(request.user):
        return JsonResponse({'success': False, 'message': 'Sem permissão'})
    
    try:
        conteudo = request.POST.get('conteudo')
        tipo = request.POST.get('tipo', 'resposta')
        tempo_gasto = request.POST.get('tempo_gasto')
        
        if not conteudo:
            return JsonResponse({'success': False, 'message': 'Conteúdo é obrigatório'})
        
        # Criar interação
        interacao = InteracaoTicket.objects.create(
            ticket=ticket,
            tipo=tipo,
            conteudo=conteudo,
            usuario=request.user,
            visivel_cliente=(tipo != 'nota_interna'),
            tempo_gasto=int(tempo_gasto) if tempo_gasto else None
        )
        
        # Processar anexos da resposta
        anexos = request.FILES.getlist('anexos')
        for anexo in anexos:
            AnexoTicket.objects.create(
                ticket=ticket,
                interacao=interacao,
                arquivo=anexo,
                usuario=request.user
            )
        
        # Atualizar status do ticket se necessário
        novo_status = request.POST.get('novo_status')
        if novo_status and novo_status != ticket.status:
            ticket.status = novo_status
            if novo_status == 'resolvido':
                ticket.resolvido_em = timezone.now()
                ticket.sla_resolucao_cumprido = ticket.resolvido_em <= ticket.prazo_resolucao
            elif novo_status == 'fechado':
                ticket.fechado_em = timezone.now()
            ticket.save()
        
        return JsonResponse({'success': True, 'message': 'Resposta adicionada com sucesso'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def atribuir_ticket(request, ticket_id):
    """Atribui um ticket a um responsável"""
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Verificar permissão
    if not ticket.pode_editar(request.user):
        return JsonResponse({'success': False, 'message': 'Sem permissão'})
    
    try:
        from django.contrib.auth.models import User
        
        responsavel_id = request.POST.get('responsavel_id')
        observacoes = request.POST.get('observacoes', '')
        
        responsavel_anterior = ticket.responsavel
        
        if responsavel_id:
            responsavel_novo = get_object_or_404(User, id=responsavel_id)
            ticket.responsavel = responsavel_novo
        else:
            responsavel_novo = None
            ticket.responsavel = None
        
        ticket.save()
        
        # Criar interação de atribuição
        InteracaoTicket.objects.create(
            ticket=ticket,
            tipo='atribuicao',
            conteudo=f"Ticket atribuído para {responsavel_novo.get_full_name() if responsavel_novo else 'Ninguém'}. {observacoes}",
            usuario=request.user,
            responsavel_anterior=responsavel_anterior,
            responsavel_novo=responsavel_novo,
            visivel_cliente=False
        )
        
        return JsonResponse({'success': True, 'message': 'Ticket atribuído com sucesso'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def download_anexo(request, anexo_id):
    """Download de anexo do ticket"""
    
    anexo = get_object_or_404(AnexoTicket, id=anexo_id)
    
    # Verificar permissão
    if not anexo.ticket.pode_visualizar(request.user):
        raise Http404
    
    try:
        response = HttpResponse(anexo.arquivo.read(), content_type=anexo.tipo_mime or 'application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{anexo.nome_original}"'
        return response
    except Exception:
        raise Http404


@login_required
def base_conhecimento(request):
    """Lista artigos da base de conhecimento"""
    
    artigos = BaseConhecimento.objects.filter(ativo=True)
    
    # Filtros
    categoria_filtro = request.GET.get('categoria')
    if categoria_filtro:
        artigos = artigos.filter(categoria_id=categoria_filtro)
    
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        artigos = artigos.filter(tipo=tipo_filtro)
    
    busca = request.GET.get('busca')
    if busca:
        artigos = artigos.filter(
            Q(titulo__icontains=busca) |
            Q(conteudo__icontains=busca) |
            Q(tags__icontains=busca)
        )
    
    # Filtrar por acesso
    if not request.user.is_superuser:
        artigos = artigos.filter(
            Q(publico=True) | Q(usuarios_acesso=request.user)
        )
    
    # Ordenação
    artigos = artigos.order_by('-destaque', '-criado_em')
    
    # Paginação
    paginator = Paginator(artigos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Artigos em destaque
    artigos_destaque = BaseConhecimento.objects.filter(
        ativo=True, destaque=True
    )[:3]
    
    # Categorias para filtro
    categorias = CategoriaTicket.objects.filter(ativo=True)
    
    context = {
        'page_obj': page_obj,
        'artigos_destaque': artigos_destaque,
        'categorias': categorias,
        'tipo_choices': BaseConhecimento.TIPOS,
        'filtros_ativos': {
            'categoria': categoria_filtro,
            'tipo': tipo_filtro,
            'busca': busca,
        }
    }
    
    return render(request, 'core/suporte/base_conhecimento.html', context)


@login_required
def artigo_conhecimento(request, artigo_id):
    """Exibe um artigo da base de conhecimento"""
    
    artigo = get_object_or_404(BaseConhecimento, id=artigo_id, ativo=True)
    
    # Verificar acesso
    if not artigo.publico and not request.user.is_superuser:
        if request.user not in artigo.usuarios_acesso.all():
            messages.error(request, 'Você não tem acesso a este artigo.')
            return redirect('base_conhecimento')
    
    # Incrementar visualizações
    artigo.visualizacoes += 1
    artigo.save()
    
    # Artigos relacionados
    artigos_relacionados = BaseConhecimento.objects.filter(
        categoria=artigo.categoria,
        ativo=True
    ).exclude(id=artigo.id)[:5]
    
    context = {
        'artigo': artigo,
        'artigos_relacionados': artigos_relacionados,
    }
    
    return render(request, 'core/suporte/artigo_conhecimento.html', context)


@login_required
@require_http_methods(["POST"])
def avaliar_artigo(request, artigo_id):
    """Avalia um artigo da base de conhecimento"""
    
    artigo = get_object_or_404(BaseConhecimento, id=artigo_id)
    util = request.POST.get('util') == 'sim'
    
    if util:
        artigo.util_sim += 1
    else:
        artigo.util_nao += 1
    
    artigo.save()
    
    return JsonResponse({'success': True, 'message': 'Avaliação registrada'})


@login_required
@require_http_methods(["POST"])
def avaliar_ticket(request, ticket_id):
    """Avalia o atendimento de um ticket"""
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Verificar se é o solicitante
    if request.user != ticket.solicitante:
        return JsonResponse({'success': False, 'message': 'Apenas o solicitante pode avaliar'})
    
    # Verificar se já foi avaliado
    if ticket.avaliacao_atendimento:
        return JsonResponse({'success': False, 'message': 'Ticket já foi avaliado'})
    
    try:
        avaliacao = int(request.POST.get('avaliacao'))
        comentario = request.POST.get('comentario', '')
        
        if avaliacao < 1 or avaliacao > 5:
            return JsonResponse({'success': False, 'message': 'Avaliação deve ser entre 1 e 5'})
        
        ticket.avaliacao_atendimento = avaliacao
        ticket.comentario_avaliacao = comentario
        ticket.avaliado_em = timezone.now()
        ticket.save()
        
        return JsonResponse({'success': True, 'message': 'Avaliação registrada com sucesso'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def relatorios_suporte(request):
    """Relatórios do sistema de suporte"""
    
    # Verificar permissão
    if not verificar_permissao(request.user, 'suporte', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar os relatórios.')
        return redirect('core:dashboard')
    
    # Período do relatório
    periodo = request.GET.get('periodo', '30')
    data_inicio = timezone.now() - timedelta(days=int(periodo))
    
    # Tickets no período
    tickets_periodo = Ticket.objects.filter(criado_em__gte=data_inicio)
    
    # Estatísticas
    total_tickets = tickets_periodo.count()
    tickets_resolvidos = tickets_periodo.filter(status='resolvido').count()
    tickets_fechados = tickets_periodo.filter(status='fechado').count()
    
    # Taxa de resolução
    taxa_resolucao = (tickets_resolvidos / total_tickets * 100) if total_tickets > 0 else 0
    
    # Tempo médio de resolução
    tickets_com_resolucao = tickets_periodo.filter(resolvido_em__isnull=False)
    tempo_medio_resolucao = 0
    if tickets_com_resolucao.exists():
        tempos = [(t.resolvido_em - t.criado_em).total_seconds() / 3600 for t in tickets_com_resolucao]
        tempo_medio_resolucao = sum(tempos) / len(tempos)
    
    # SLA
    sla_primeira_resposta = tickets_periodo.filter(
        sla_primeira_resposta_cumprido=True
    ).count()
    sla_resolucao = tickets_periodo.filter(
        sla_resolucao_cumprido=True
    ).count()
    
    # Avaliação média
    avaliacao_media = tickets_periodo.filter(
        avaliacao_atendimento__isnull=False
    ).aggregate(media=Avg('avaliacao_atendimento'))['media'] or 0
    
    # Tickets por categoria
    tickets_por_categoria = tickets_periodo.values(
        'categoria__nome'
    ).annotate(total=Count('id')).order_by('-total')
    
    # Tickets por responsável
    tickets_por_responsavel = tickets_periodo.filter(
        responsavel__isnull=False
    ).values(
        'responsavel__first_name', 'responsavel__last_name'
    ).annotate(total=Count('id')).order_by('-total')
    
    context = {
        'periodo': periodo,
        'total_tickets': total_tickets,
        'tickets_resolvidos': tickets_resolvidos,
        'tickets_fechados': tickets_fechados,
        'taxa_resolucao': round(taxa_resolucao, 1),
        'tempo_medio_resolucao': round(tempo_medio_resolucao, 1),
        'sla_primeira_resposta': sla_primeira_resposta,
        'sla_resolucao': sla_resolucao,
        'avaliacao_media': round(avaliacao_media, 1),
        'tickets_por_categoria': tickets_por_categoria,
        'tickets_por_responsavel': tickets_por_responsavel,
    }
    
    return render(request, 'core/suporte/relatorios.html', context)


@login_required
def configuracoes_suporte(request):
    """Configurações do sistema de suporte"""
    
    # Verificar permissão
    if not request.user.is_superuser:
        messages.error(request, 'Apenas administradores podem acessar as configurações.')
        return redirect('dashboard_suporte')
    
    config = ConfiguracaoSuporte.get_configuracao()
    
    if request.method == 'POST':
        try:
            # Atualizar configurações
            config.horario_inicio = request.POST.get('horario_inicio')
            config.horario_fim = request.POST.get('horario_fim')
            config.dias_funcionamento = request.POST.get('dias_funcionamento')
            config.notificar_novo_ticket = 'notificar_novo_ticket' in request.POST
            config.notificar_resposta_cliente = 'notificar_resposta_cliente' in request.POST
            config.notificar_sla_violado = 'notificar_sla_violado' in request.POST
            config.email_suporte = request.POST.get('email_suporte')
            config.whatsapp_ativo = 'whatsapp_ativo' in request.POST
            config.whatsapp_numero = request.POST.get('whatsapp_numero')
            config.chat_ativo = 'chat_ativo' in request.POST
            config.base_conhecimento_ativa = 'base_conhecimento_ativa' in request.POST
            config.sugerir_artigos = 'sugerir_artigos' in request.POST
            config.sla_resposta_padrao = int(request.POST.get('sla_resposta_padrao'))
            config.sla_resolucao_padrao = int(request.POST.get('sla_resolucao_padrao'))
            
            config.save()
            
            messages.success(request, 'Configurações salvas com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao salvar configurações: {str(e)}')
    
    context = {
        'config': config,
    }
    
    return render(request, 'core/suporte/configuracoes.html', context)


# API para integração com WhatsApp e outros sistemas
@csrf_exempt
@require_http_methods(["POST"])
def api_criar_ticket(request):
    """API para criar ticket via integração externa"""
    
    try:
        data = json.loads(request.body)
        
        # Validar dados obrigatórios
        required_fields = ['titulo', 'descricao', 'categoria_id', 'solicitante_email']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'message': f'Campo {field} é obrigatório'})
        
        # Buscar usuário solicitante
        from django.contrib.auth.models import User
        try:
            solicitante = User.objects.get(email=data['solicitante_email'])
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Usuário não encontrado'})
        
        # Buscar categoria
        try:
            categoria = CategoriaTicket.objects.get(id=data['categoria_id'])
        except CategoriaTicket.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Categoria não encontrada'})
        
        # Criar ticket
        ticket = Ticket.objects.create(
            titulo=data['titulo'],
            descricao=data['descricao'],
            categoria=categoria,
            prioridade=data.get('prioridade', 'normal'),
            canal=data.get('canal', 'whatsapp'),
            solicitante=solicitante
        )
        
        return JsonResponse({
            'success': True,
            'ticket_id': ticket.id,
            'numero': ticket.numero,
            'message': 'Ticket criado com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
@require_http_methods(["GET"])
def api_status_ticket(request, numero):
    """API para consultar status de ticket"""
    
    try:
        ticket = get_object_or_404(Ticket, numero=numero)
        
        return JsonResponse({
            'success': True,
            'ticket': {
                'numero': ticket.numero,
                'titulo': ticket.titulo,
                'status': ticket.get_status_display(),
                'prioridade': ticket.get_prioridade_display(),
                'categoria': ticket.categoria.nome,
                'criado_em': ticket.criado_em.isoformat(),
                'atualizado_em': ticket.atualizado_em.isoformat(),
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})