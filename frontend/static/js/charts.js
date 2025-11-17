// Chart configurations and utilities for analytics

// Initialize retention curve chart
function createRetentionChart(canvasId, retentionData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: retentionData.days || [],
            datasets: [{
                label: 'Retention Probability',
                data: retentionData.retention || [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            weight: 600
                        },
                        color: '#2d3748'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 600
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            return `Retention: ${Math.round(context.parsed.y * 100)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Days Since Learning',
                        font: {
                            size: 13,
                            weight: 600
                        },
                        color: '#4a5568'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Retention %',
                        font: {
                            size: 13,
                            weight: 600
                        },
                        color: '#4a5568'
                    },
                    min: 0,
                    max: 1,
                    ticks: {
                        callback: function(value) {
                            return Math.round(value * 100) + '%';
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Create performance over time chart
function createPerformanceChart(canvasId, performanceData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: performanceData.dates || [],
            datasets: [{
                label: 'Daily Score',
                data: performanceData.scores || [],
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: '#667eea',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Create mastery radar chart
function createMasteryRadar(canvasId, masteryData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: masteryData.topics || [],
            datasets: [{
                label: 'Mastery Level',
                data: masteryData.levels || [],
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                borderColor: '#667eea',
                borderWidth: 3,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    min: 0,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Create time distribution pie chart
function createTimeDistribution(canvasId, timeData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: timeData.categories || ['Math', 'Science', 'CS', 'Other'],
            datasets: [{
                data: timeData.hours || [10, 8, 12, 5],
                backgroundColor: [
                    '#667eea',
                    '#48bb78',
                    '#f56565',
                    '#ed8936'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 13,
                            weight: 600
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value}h (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Create streak calendar heatmap
function createStreakCalendar(containerId, streakData) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const weeks = 12;
    const days = 7;
    
    let html = '<div style="display: grid; grid-template-columns: repeat(12, 1fr); gap: 4px;">';
    
    for (let week = 0; week < weeks; week++) {
        for (let day = 0; day < days; day++) {
            const index = week * days + day;
            const activity = streakData[index] || 0;
            const color = getActivityColor(activity);
            
            html += `<div style="
                width: 100%;
                aspect-ratio: 1;
                background: ${color};
                border-radius: 4px;
                cursor: pointer;
                transition: transform 0.2s;
            " title="${activity} lessons"></div>`;
        }
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function getActivityColor(activity) {
    if (activity === 0) return '#f0f0f0';
    if (activity <= 2) return '#c6e2ff';
    if (activity <= 4) return '#84c5ff';
    if (activity <= 6) return '#4ba5ff';
    return '#667eea';
}

// Utility function to generate sample data
function generateSampleData(days = 30) {
    return {
        retention: {
            days: Array.from({length: days}, (_, i) => i),
            retention: Array.from({length: days}, (_, i) => 
                Math.max(0.1, 1 - (i * 0.03) + (Math.random() * 0.1))
            )
        },
        performance: {
            dates: Array.from({length: 7}, (_, i) => {
                const date = new Date();
                date.setDate(date.getDate() - (6 - i));
                return date.toLocaleDateString('en-US', { weekday: 'short' });
            }),
            scores: Array.from({length: 7}, () => 
                Math.floor(Math.random() * 30 + 70)
            )
        },
        mastery: {
            topics: ['Algebra', 'Geometry', 'Calculus', 'Statistics', 'Logic'],
            levels: [85, 72, 65, 90, 78]
        },
        time: {
            categories: ['Math', 'Science', 'CS', 'Other'],
            hours: [10, 8, 12, 5]
        },
        streak: Array.from({length: 84}, () => Math.floor(Math.random() * 8))
    };
}

// Export functions
window.chartUtils = {
    createRetentionChart,
    createPerformanceChart,
    createMasteryRadar,
    createTimeDistribution,
    createStreakCalendar,
    generateSampleData
};