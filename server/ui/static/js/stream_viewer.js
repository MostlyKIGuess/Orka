function toggleSLAM(streamId, enable) {
    fetch(`/api/streams/${streamId}/slam/${enable ? 'on' : 'off'}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(`Failed to ${enable ? 'enable' : 'disable'} SLAM: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error toggling SLAM:', error);
        alert('Error toggling SLAM. See console for details.');
    });
}

function toggleRecording(streamId, action) {
    fetch(`/api/streams/${streamId}/record/${action}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.recording_status) {
            window.location.reload();
        } else {
            alert(`Failed to ${action === 'on' ? 'start' : 'stop'} recording`);
        }
    })
    .catch(error => {
        console.error('Error toggling recording:', error);
        alert('Error toggling recording. See console for details.');
    });
}

// Update images and data periodically
function updateStreamData(streamId, slamActive) {
    const timestamp = Date.now();
    
    // Update live stream
    document.getElementById('liveStream').src = `/api/streams/${streamId}/live?t=${timestamp}`;
    
    if (slamActive) {
        // Update SLAM visualization
        document.getElementById('slamViz').src = `/api/streams/${streamId}/slam_view?t=${timestamp}`;
        document.getElementById('slamMap').src = `/api/streams/${streamId}/slam_map?t=${timestamp}`;
        
        // Update SLAM data
        fetch(`/api/streams/${streamId}/slam_data?t=${timestamp}`)
            .then(response => response.json())
            .then(data => {
                if (data.slam_active) {
                    document.getElementById('featureCount').textContent = data.feature_count || 0;
                    document.getElementById('trajectoryLength').textContent = data.trajectory_length || 0;
                    
                    const date = new Date(data.timestamp * 1000);
                    document.getElementById('lastUpdate').textContent = 
                        date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                }
            })
            .catch(error => console.error('Error fetching SLAM data:', error));
    }
}

// Initialize periodic updates
function initializeStreamUpdates(streamId, slamActive) {
    setInterval(() => updateStreamData(streamId, slamActive), 100);
}
