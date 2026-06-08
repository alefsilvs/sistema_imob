from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('saas', '0007_evolutioninstance_evolutionmessage_evolutionwebhook'),
        ('contratos', '0002_contrato_tenant'),
        ('core', '0017_alter_pessoa_agencia_alter_pessoa_banco_and_more'),
        ('financeiro', '0021_alter_caixamovimento_options_and_more'),
        ('notificacoes', '0003_notificacao_banca_feira_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CobrancaAutomaticaLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('ALUGUEL', 'Aluguel'), ('IPTU_CONTRATO', 'IPTU (Contrato)'), ('IPTU_PARCELA', 'IPTU (Parcela)')], max_length=20)),
                ('nivel', models.PositiveSmallIntegerField()),
                ('canal', models.CharField(default='WHATSAPP', max_length=20)),
                ('destinatario', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('ENVIADA', 'Enviada'), ('ERRO', 'Erro'), ('SIMULADA', 'Simulada')], max_length=20)),
                ('provider', models.CharField(blank=True, max_length=50)),
                ('provider_message_id', models.CharField(blank=True, max_length=255)),
                ('erro', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('contrato', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contratos.contrato')),
                ('inquilino', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.inquilino')),
                ('parcela', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='financeiro.parcela')),
                ('parcela_iptu', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='financeiro.parcelaiptu')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='saas.tenant')),
            ],
            options={
                'verbose_name': 'Cobrança Automática (Log)',
                'verbose_name_plural': 'Cobranças Automáticas (Logs)',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='cobrancaautomaticalog',
            constraint=models.UniqueConstraint(condition=Q(('parcela__isnull', False)), fields=('tenant', 'tipo', 'nivel', 'parcela'), name='uniq_cobranca_auto_parcela_nivel'),
        ),
        migrations.AddConstraint(
            model_name='cobrancaautomaticalog',
            constraint=models.UniqueConstraint(condition=Q(('parcela_iptu__isnull', False)), fields=('tenant', 'tipo', 'nivel', 'parcela_iptu'), name='uniq_cobranca_auto_parcela_iptu_nivel'),
        ),
    ]
