/* ===== SERVICE WORKER - PWA ===== */

const CACHE_NAME = 'sistema-imo-v1.0.0';
const urlsToCache = [
    '/',
    '/static/css/responsive.css',
    '/static/js/responsive.js',
    '/static/css/bootstrap.min.css',
    '/static/js/bootstrap.bundle.min.js',
    '/static/js/chart.min.js',
    '/static/css/fontawesome.min.css',
    '/static/webfonts/fa-solid-900.woff2',
    '/static/webfonts/fa-regular-400.woff2',
    '/static/webfonts/fa-brands-400.woff2',
    // Adicionar outras URLs importantes aqui
];

// Instalação do Service Worker
self.addEventListener('install', function(event) {
    console.log('Service Worker: Instalando...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Service Worker: Cache aberto');
                return cache.addAll(urlsToCache);
            })
            .catch(function(error) {
                console.log('Service Worker: Erro ao cachear arquivos', error);
            })
    );
    
    // Forçar ativação imediata
    self.skipWaiting();
});

// Ativação do Service Worker
self.addEventListener('activate', function(event) {
    console.log('Service Worker: Ativando...');
    
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    // Remover caches antigos
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Removendo cache antigo', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    // Assumir controle de todas as páginas
    self.clients.claim();
});

// Interceptar requisições
self.addEventListener('fetch', function(event) {
    // Ignorar requisições não-GET
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Ignorar requisições para APIs externas
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Retornar do cache se disponível
                if (response) {
                    console.log('Service Worker: Servindo do cache', event.request.url);
                    return response;
                }
                
                // Buscar da rede
                return fetch(event.request)
                    .then(function(response) {
                        // Verificar se a resposta é válida
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clonar a resposta
                        const responseToCache = response.clone();
                        
                        // Adicionar ao cache
                        caches.open(CACHE_NAME)
                            .then(function(cache) {
                                cache.put(event.request, responseToCache);
                            });
                        
                        return response;
                    })
                    .catch(function(error) {
                        console.log('Service Worker: Erro na requisição', error);
                        
                        // Retornar página offline para navegação
                        if (event.request.destination === 'document') {
                            return caches.match('/offline.html');
                        }
                        
                        // Retornar imagem padrão para imagens
                        if (event.request.destination === 'image') {
                            return caches.match('/static/img/offline.svg');
                        }
                        
                        throw error;
                    });
            })
    );
});

// Sincronização em background
self.addEventListener('sync', function(event) {
    console.log('Service Worker: Sincronização em background', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

// Notificações push
self.addEventListener('push', function(event) {
    console.log('Service Worker: Notificação push recebida');
    
    const options = {
        body: event.data ? event.data.text() : 'Nova notificação do Sistema Imobiliário',
        icon: '/static/img/icon-192x192.png',
        badge: '/static/img/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Ver detalhes',
                icon: '/static/img/checkmark.png'
            },
            {
                action: 'close',
                title: 'Fechar',
                icon: '/static/img/xmark.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Sistema Imobiliário', options)
    );
});

// Clique em notificação
self.addEventListener('notificationclick', function(event) {
    console.log('Service Worker: Clique em notificação', event.notification.tag);
    
    event.notification.close();
    
    if (event.action === 'explore') {
        // Abrir a aplicação
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'close') {
        // Apenas fechar a notificação
        event.notification.close();
    } else {
        // Clique na notificação (não em ação)
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Função para sincronização em background
function doBackgroundSync() {
    return new Promise(function(resolve, reject) {
        // Implementar lógica de sincronização
        // Por exemplo, enviar dados pendentes para o servidor
        
        // Buscar dados pendentes do IndexedDB
        // Enviar para o servidor
        // Limpar dados após envio bem-sucedido
        
        console.log('Service Worker: Sincronização concluída');
        resolve();
    });
}

// Atualização do Service Worker
self.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// Cache de estratégias específicas
const cacheStrategies = {
    // Cache First - para recursos estáticos
    cacheFirst: function(request) {
        return caches.match(request)
            .then(function(response) {
                return response || fetch(request);
            });
    },
    
    // Network First - para dados dinâmicos
    networkFirst: function(request) {
        return fetch(request)
            .then(function(response) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                    .then(function(cache) {
                        cache.put(request, responseClone);
                    });
                return response;
            })
            .catch(function() {
                return caches.match(request);
            });
    },
    
    // Stale While Revalidate - para recursos que podem estar desatualizados
    staleWhileRevalidate: function(request) {
        const fetchPromise = fetch(request)
            .then(function(response) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                    .then(function(cache) {
                        cache.put(request, responseClone);
                    });
                return response;
            });
        
        return caches.match(request)
            .then(function(response) {
                return response || fetchPromise;
            });
    }
};

// Limpeza periódica do cache
function cleanupCache() {
    const maxCacheSize = 50; // MB
    const maxCacheAge = 7 * 24 * 60 * 60 * 1000; // 7 dias
    
    caches.open(CACHE_NAME)
        .then(function(cache) {
            cache.keys()
                .then(function(requests) {
                    requests.forEach(function(request) {
                        cache.match(request)
                            .then(function(response) {
                                const dateHeader = response.headers.get('date');
                                const cacheDate = new Date(dateHeader);
                                const now = new Date();
                                
                                // Remover se muito antigo
                                if (now - cacheDate > maxCacheAge) {
                                    cache.delete(request);
                                }
                            });
                    });
                });
        });
}

// Executar limpeza a cada hora
setInterval(cleanupCache, 60 * 60 * 1000);