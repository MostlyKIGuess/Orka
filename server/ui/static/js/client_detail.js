document.addEventListener('DOMContentLoaded', function() {
    window.speakText = function(clientId) {
        const textElem = document.getElementById('text-to-speak');
        const agentElem = document.getElementById('agent-name');
        const resultElem = document.getElementById('speak-result');
        
        if (!textElem || !textElem.value.trim()) {
            resultElem.innerHTML = '<div class="error">Please enter text to speak.</div>';
            return;
        }
        
        const text = textElem.value.trim();
        const agent = agentElem?.value.trim() || 'Server';
        
        const button = document.getElementById('speak-button');
        if (button) button.disabled = true;
        
        resultElem.innerHTML = '<div class="loading">Sending request...</div>';
        
        fetch(`/clients/${clientId}/commands/speak_text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                agent_name: agent
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                resultElem.innerHTML = `<div class="success">Successfully spoken: "${text}"</div>`;
            } else {
                resultElem.innerHTML = `<div class="error">Error: ${data.error_message || 'Unknown error'}</div>`;
            }
        })
        .catch(error => {
            resultElem.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        })
        .finally(() => {
            if (button) button.disabled = false;
        });
    };
    
    window.captureImage = function(clientId) {
        const resultElem = document.getElementById('capture-result');
        const imageContainer = document.getElementById('image-container');
        
        const button = document.getElementById('capture-button');
        if (button) button.disabled = true;
        
        resultElem.innerHTML = '<div class="loading">Requesting image capture...</div>';
        imageContainer.innerHTML = '';
        
        fetch(`/clients/${clientId}/commands/capture_image`, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                resultElem.innerHTML = `<div class="success">Image captured successfully!</div>`;
                
                // For now, we don't have a direct way to get the image in the UI
                // We could enhance this by having an endpoint that serves the latest image
                // For now, just show a placeholder message
                imageContainer.innerHTML = `
                    <p>Image saved on server in output directory.</p>
                    <p>Image format: ${data.data?.format || 'jpg'}</p>
                `;
            } else {
                resultElem.innerHTML = `<div class="error">Error: ${data.error_message || 'Unknown error'}</div>`;
            }
        })
        .catch(error => {
            resultElem.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        })
        .finally(() => {
            if (button) button.disabled = false;
        });
    };
    
    window.startStream = function(clientId) {
        const streamSelect = document.getElementById('stream-quality');
        const fps = streamSelect ? parseInt(streamSelect.value, 10) : 15;
        
        fetch(`/clients/${clientId}/commands/start_video_stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fps: fps,
                quality: 75,
                width: 640,
                height: 480
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                alert(`Stream started with ID: ${data.data.stream_id}. Refresh page to see it in the streams list.`);
                // Auto refresh after 2 seconds
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                alert(`Error starting stream: ${data.error_message || 'Unknown error'}`);
            }
        })
        .catch(error => {
            alert(`Error starting stream: ${error.message}`);
        });
    };
    
 window.toggleRecording = function(streamId, action) {
    fetch(`/streams/${streamId}/record/${action}`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.recording_status === 'enabled') {
            alert(`Recording started for stream ${streamId}`);
        } else if (data.recording_status === 'stopped') {
            alert(`Recording stopped for stream ${streamId}. File saved at: ${data.file}`);
        } else {
            alert(`Recording status: ${data.recording_status}. ${data.message || ''}`);
        }
        // Refresh to update UI
        window.location.reload();
    })
    .catch(error => {
        console.error('Error toggling recording:', error);
        alert(`Error toggling recording: ${error.message}`);
    });
};


    window.toggleSLAM = function(streamId, enable) {
        console.log(`Toggling SLAM ${enable ? 'on' : 'off'} for stream ${streamId}`);
        
        fetch(`/api/streams/${streamId}/slam/${enable ? 'on' : 'off'}`, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert(`SLAM ${enable ? 'enabled' : 'disabled'} successfully for stream ${streamId}`);
                // Reload the page to show updated state
                window.location.reload();
            } else {
                alert(`Failed to ${enable ? 'enable' : 'disable'} SLAM: ${data.message || 'Unknown error'}`);
            }
        })
        .catch(error => {
            console.error('Error toggling SLAM:', error);
            alert(`Error toggling SLAM: ${error.message}`);
        });
    };
});
