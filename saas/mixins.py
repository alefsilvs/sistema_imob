from django.db import models
from django.core.exceptions import ValidationError

class TenantMixin(models.Model):
    """
    Mixin para adicionar funcionalidade de tenant aos modelos
    """
    tenant = models.ForeignKey('saas.Tenant', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Tenant')
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Se não há tenant definido e há um request com tenant, usar o tenant do request
        if not self.tenant and hasattr(self, '_request') and hasattr(self._request, 'tenant'):
            self.tenant = self._request.tenant
        super().save(*args, **kwargs)
    
    @classmethod
    def filter_by_tenant(cls, tenant):
        """
        Filtra objetos pelo tenant
        """
        if tenant:
            return cls.objects.filter(tenant=tenant)
        return cls.objects.none()

class TenantQuerySet(models.QuerySet):
    """
    QuerySet personalizado para filtrar automaticamente por tenant
    """
    def __init__(self, *args, **kwargs):
        self._tenant = None
        super().__init__(*args, **kwargs)
    
    def filter_by_tenant(self, tenant):
        """
        Filtra por tenant
        """
        if tenant:
            return self.filter(tenant=tenant)
        return self.none()
    
    def set_tenant(self, tenant):
        """
        Define o tenant para este queryset
        """
        self._tenant = tenant
        return self
    
    def _clone(self):
        clone = super()._clone()
        clone._tenant = self._tenant
        return clone

class TenantManager(models.Manager):
    """
    Manager personalizado para filtrar automaticamente por tenant
    """
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
    
    def filter_by_tenant(self, tenant):
        """
        Filtra por tenant
        """
        return self.get_queryset().filter_by_tenant(tenant)
    
    def for_tenant(self, tenant):
        """
        Retorna objetos para um tenant específico
        """
        if tenant:
            return self.get_queryset().filter(tenant=tenant)
        return self.get_queryset().none()

class TenantViewMixin:
    """
    Mixin para views que precisam filtrar por tenant
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return queryset.filter(tenant=self.request.tenant)
        return queryset.none()
    
    def form_valid(self, form):
        # Definir tenant no objeto antes de salvar
        if hasattr(self.request, 'tenant') and self.request.tenant:
            form.instance.tenant = self.request.tenant
        return super().form_valid(form)