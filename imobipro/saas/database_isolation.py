"""
Sistema de isolamento de banco de dados por tenant usando schemas PostgreSQL
"""

import logging
from django.db import connection, transaction
from django.apps import apps
from django.conf import settings

# Importação condicional do psycopg2
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

logger = logging.getLogger(__name__)

class TenantDatabaseManager:
    """
    Gerencia a criação e configuração de schemas de banco de dados por tenant
    """
    
    def __init__(self):
        self.connection = connection
    
    def create_tenant_schema(self, tenant):
        """
        Cria um schema isolado para o tenant
        """
        if not HAS_PSYCOPG2 or connection.vendor != 'postgresql':
            logger.info(f"PostgreSQL não disponível - usando isolamento por tenant_id para {tenant.slug}")
            return True
            
        try:
            schema_name = f"tenant_{tenant.id}"
            
            with connection.cursor() as cursor:
                # Criar schema
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                logger.info(f"Schema {schema_name} criado para tenant {tenant.slug}")
                
                # Criar tabelas no schema
                self._create_tenant_tables(cursor, schema_name)
                
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar schema para tenant {tenant.slug}: {str(e)}")
            return False
    
    def delete_tenant_schema(self, tenant):
        """
        Remove o schema do tenant
        """
        if not HAS_PSYCOPG2 or connection.vendor != 'postgresql':
            logger.info(f"PostgreSQL não disponível - schema não será removido para {tenant.slug}")
            return True
            
        try:
            schema_name = f"tenant_{tenant.id}"
            
            with connection.cursor() as cursor:
                cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
                logger.info(f"Schema {schema_name} removido para tenant {tenant.slug}")
                
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover schema para tenant {tenant.slug}: {str(e)}")
            return False
    
    def set_tenant_schema(self, tenant_id):
        """
        Define o schema do tenant para a conexão atual
        """
        try:
            with connection.cursor() as cursor:
                if connection.vendor != 'postgresql':
                    logger.debug(f"SQLite detectado - schema não alterado (tenant_id: {tenant_id})")
                    return

                if not tenant_id:
                    cursor.execute("SET search_path TO public")
                    logger.debug("Schema definido para: public")
                    return

                schema_name = f"tenant_{tenant_id}"
                schema_exists = False
                try:
                    cursor.execute(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s)",
                        [schema_name],
                    )
                    schema_exists = bool(cursor.fetchone()[0])
                except Exception:
                    schema_exists = False

                if not schema_exists:
                    cursor.execute("SET search_path TO public")
                    logger.warning(f"Schema {schema_name} não existe. Usando public.")
                    return

                cursor.execute(f"SET search_path TO {schema_name}, public")
                logger.debug(f"Schema definido para: {schema_name}")
        except Exception as e:
            try:
                with connection.cursor() as cursor:
                    if connection.vendor == 'postgresql':
                        cursor.execute("SET search_path TO public")
            except Exception:
                pass
            logger.error(f"Erro ao definir schema do tenant {tenant_id}: {str(e)}")
            return
    
    def _create_tenant_tables(self, cursor, schema_name):
        """
        Cria tabelas básicas no schema do tenant copiando da estrutura pública
        """
        # Lista de tabelas que devem ser isoladas por tenant
        tenant_tables = [
            'imoveis_imovel',
            'imoveis_foto',
            'imoveis_contrato',
            'documentos_documento',
            'core_perfilusuario',
            'assinaturas_assinatura'
        ]
        
        for table_name in tenant_tables:
            try:
                # Verificar se a tabela existe no schema público
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, [table_name])
                
                if cursor.fetchone()[0]:
                    # Criar tabela no schema do tenant baseada na estrutura pública
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} 
                        (LIKE public.{table_name} INCLUDING ALL)
                    """)
                    logger.debug(f"Tabela {table_name} criada no schema {schema_name}")
                    
            except Exception as e:
                logger.warning(f"Erro ao criar tabela {table_name} no schema {schema_name}: {str(e)}")


class TenantSchemaMiddleware:
    """
    Middleware para definir automaticamente o schema do tenant baseado na sessão
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.db_manager = TenantDatabaseManager()
    
    def __call__(self, request):
        path = getattr(request, "path", "") or ""
        exempt_prefixes = (
            "/admin/",
            "/accounts/",
            "/saas/",
            "/static/",
            "/media/",
        )
        force_public_schema = path.startswith(exempt_prefixes)

        session = getattr(request, "session", None)
        tenant_id = None if force_public_schema else (session.get("tenant_id") if session else None)

        if not force_public_schema and not tenant_id:
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                try:
                    from saas.models import Tenant
                    if getattr(user, "is_superuser", False):
                        tenant = Tenant.objects.filter(usuario_admin=user).first() or Tenant.objects.first()
                    else:
                        tenant = Tenant.objects.filter(usuario_admin=user).first()
                    if tenant:
                        tenant_id = tenant.id
                        try:
                            if session is not None:
                                session["tenant_id"] = tenant_id
                                session.modified = True
                        except Exception:
                            pass
                except Exception:
                    tenant_id = None

        try:
            self.db_manager.set_tenant_schema(tenant_id)
            return self.get_response(request)
        finally:
            self.db_manager.set_tenant_schema(None)


# Funções utilitárias para uso em views e services
def get_current_tenant_schema():
    """
    Retorna o schema atual do tenant
    """
    with connection.cursor() as cursor:
        cursor.execute("SHOW search_path")
        search_path = cursor.fetchone()[0]
        
        if 'tenant_' in search_path:
            return search_path.split(',')[0].strip()
        return 'public'


def switch_to_tenant_schema(tenant_id):
    """
    Muda para o schema do tenant especificado
    """
    db_manager = TenantDatabaseManager()
    db_manager.set_tenant_schema(tenant_id)


def switch_to_public_schema():
    """
    Volta para o schema público
    """
    db_manager = TenantDatabaseManager()
    db_manager.set_tenant_schema(None)
