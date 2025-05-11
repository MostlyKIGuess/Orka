document.addEventListener('DOMContentLoaded', function() {
    //  the "last seen" times periodically
    function updateLastSeenTimes() {
        const elements = document.querySelectorAll('.last-seen');
        elements.forEach(el => {
            const seconds = parseFloat(el.dataset.seconds) + 1;
            el.dataset.seconds = seconds;
            
            if (seconds < 60) {
                el.textContent = `${Math.round(seconds)}s ago`;
            } else if (seconds < 3600) {
                el.textContent = `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s ago`;
            } else {
                el.textContent = `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m ago`;
            }
        });
    }

    // Auto-refresh data every 10 seconds
    function refreshDashboard() {
        fetch('/clients')
            .then(response => response.json())
            .then(clients => {
                const container = document.getElementById('clients-container');
                const count = document.getElementById('clients-count');
                
                count.innerHTML = `<p>Total clients: <span class="badge">${Object.keys(clients).length}</span></p>`;
                
                // If no clients, show message
                if (Object.keys(clients).length === 0) {
                    count.innerHTML += `
                    <div class="no-clients">
                        <p>No clients connected. Run a client with:</p>
                        <pre>python client/main_client.py --server ws://${window.location.host}</pre>
                    </div>`;
                    container.innerHTML = '';
                    return;
                }
                
                // Get existing client IDs in the DOM
                const existingCards = Array.from(container.querySelectorAll('.client-card'))
                    .map(card => card.dataset.clientId);
                
                // Get new client IDs from the data
                const newClientIds = Object.keys(clients);
                
                // Remove clients that are no longer connected
                for (const existingId of existingCards) {
                    if (!newClientIds.includes(existingId)) {
                        const card = container.querySelector(`.client-card[data-client-id="${existingId}"]`);
                        if (card) {
                            card.classList.add('fade-out');
                            setTimeout(() => {
                                card.remove();
                            }, 500);
                        }
                    }
                }
                
                for (const clientId of newClientIds) {
                    // If client already exists, update
                    const existingCard = container.querySelector(`.client-card[data-client-id="${clientId}"]`);
                    
                    if (existingCard) {
                        // Update last seen
                        const lastSeenEl = existingCard.querySelector('.last-seen');
                        if (lastSeenEl) {
                            lastSeenEl.dataset.seconds = clients[clientId].last_seen_ago_s;
                            updateLastSeenTimes();
                        }
                    } else {
                        // Client doesn't exist, fetch the HTML for the new client and add it
                        fetch(`/client_card_html/${clientId}`)
                            .then(response => response.text())
                            .then(html => {
                                const tempDiv = document.createElement('div');
                                tempDiv.innerHTML = html.trim();
                                const newCard = tempDiv.firstChild;
                                newCard.classList.add('fade-in');
                                container.appendChild(newCard);
                            })
                            .catch(err => console.error('Error fetching client card HTML:', err));
                    }
                }
            })
            .catch(err => console.error('Error refreshing dashboard:', err));
    }

    updateLastSeenTimes();
    
    setInterval(updateLastSeenTimes, 1000);  // Update every second
    setInterval(refreshDashboard, 10000);    // Refresh every 10 seconds
});
