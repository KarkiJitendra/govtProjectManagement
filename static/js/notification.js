// static/js/notifications.js
document.addEventListener('DOMContentLoaded', function () {
    // Ensure current_user is available if needed, e.g. via a global JS var or data attribute
    // const currentUsername = document.body.dataset.currentUsername; // Example if set on body

    const notificationSocketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const notificationSocketUrl = notificationSocketProtocol + '//' + window.location.host + '/ws/notifications/';
    
    let notificationSocket;

    function connectNotificationSocket() {
        notificationSocket = new WebSocket(notificationSocketUrl);

        notificationSocket.onopen = function(e) {
            console.log('Notification WebSocket connection established.');
        };

        notificationSocket.onmessage = function(e) {
            try {
                const data = JSON.parse(e.data);
                console.log('Notification received:', data);

                if (data.type === 'new_message_notification') {
                    handleNewMessageNotification(data);
                } else if (data.type === 'unread_count_update') {
                    handleUnreadCountUpdate(data);
                }
            } catch (error) {
                console.error("Error parsing notification data: ", error, e.data);
            }
        };

        notificationSocket.onclose = function(e) {
            console.error('Notification WebSocket connection closed. Attempting to reconnect...');
            setTimeout(connectNotificationSocket, 5000); // Reconnect after 5 seconds
        };

        notificationSocket.onerror = function(e) {
            console.error('Notification WebSocket error:', e);
            // notificationSocket.close(); // Optional: trigger onclose for reconnect logic
        };
    }

    connectNotificationSocket(); // Initial connection attempt


    function handleNewMessageNotification(data) {
        // data contains: sender_username, unread_from_sender_count, total_unread_count_for_receiver

        // Update for list_users.html (if on that page)
        const userListItem = document.querySelector(`.user-chat-item[data-username="${data.sender_username}"]`);
        if (userListItem) {
            const unreadBadge = userListItem.querySelector('.unread-count-badge');
            if (unreadBadge) {
                unreadBadge.textContent = `🔔 ${data.unread_from_sender_count} New`;
                unreadBadge.style.display = data.unread_from_sender_count > 0 ? 'inline-flex' : 'none';
            }
        }

        // Update for dashboard.html (if on that page)
        const totalUnreadBadgeDashboard = document.getElementById('total-unread-badge-dashboard');
        if (totalUnreadBadgeDashboard) {
            totalUnreadBadgeDashboard.textContent = data.total_unread_count_for_receiver;
            totalUnreadBadgeDashboard.style.display = data.total_unread_count_for_receiver > 0 ? 'inline-flex' : 'none';
        }

        // Optional: Show a toast notification
        // if (typeof showToast === "function") { // If you have a global toast function
        //    showToast(`New message from ${data.sender_username}: ${data.message_preview}`);
        // }
        console.log(`Toast (simulated): New message from ${data.sender_username}`);
    }

    function handleUnreadCountUpdate(data) {
        // data contains: event_trigger, chat_partner_username, unread_from_partner_count, new_total_unread_count

        if (data.event_trigger === 'conversation_partner_messages_read') {
            // Update for list_users.html
            const userListItem = document.querySelector(`.user-chat-item[data-username="${data.chat_partner_username}"]`);
            if (userListItem) {
                const unreadBadge = userListItem.querySelector('.unread-count-badge');
                if (unreadBadge) {
                    unreadBadge.textContent = `🔔 ${data.unread_from_partner_count} New`; // Should be 0
                    unreadBadge.style.display = data.unread_from_partner_count > 0 ? 'inline-flex' : 'none';
                }
            }
        }

        // Update total unread count on dashboard.html
        const totalUnreadBadgeDashboard = document.getElementById('total-unread-badge-dashboard');
        if (totalUnreadBadgeDashboard) {
            totalUnreadBadgeDashboard.textContent = data.new_total_unread_count;
            totalUnreadBadgeDashboard.style.display = data.new_total_unread_count > 0 ? 'inline-flex' : 'none';
        }
        console.log(`Counts updated. Partner: ${data.chat_partner_username}, Total: ${data.new_total_unread_count}`);
    }
});