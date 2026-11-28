// HHectare Web Push Service Worker
self.addEventListener('push', function(event) {
    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data = {
                title: 'HHectare Notification',
                body: event.data.text()
            };
        }
    }

    const title = data.title || 'New Notification - HHectare';
    const options = {
        body: data.body || 'You have a new update on your property listing.',
        icon: data.icon || '/static/img/logo.png',
        badge: data.badge || '/static/img/logo.png',
        data: {
            url: data.url || '/agent/leads/'
        },
        vibrate: [200, 100, 200],
        tag: data.tag || 'hhectare-inquiry',
        renotify: true
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    const targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/agent/leads/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            for (let i = 0; i < clientList.length; i++) {
                let client = clientList[i];
                if (client.url.includes(targetUrl) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
