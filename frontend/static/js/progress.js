// Progress tracking and analytics
class ProgressTracker {
    constructor() {
        this.sessionData = {
            lessons_completed: 0,
            questions_answered: 0,
            correct_answers: 0,
            total_time: 0,
            streak_days: 0,
            last_activity: null
        };
        
        this.loadFromStorage();
    }
    
    loadFromStorage() {
        const stored = localStorage.getItem('pathlearn_progress');
        if (stored) {
            this.sessionData = JSON.parse(stored);
        }
    }
    
    saveToStorage() {
        localStorage.setItem('pathlearn_progress', JSON.stringify(this.sessionData));
    }
    
    recordLessonComplete(lessonId, stats) {
        this.sessionData.lessons_completed++;
        this.sessionData.questions_answered += stats.total_questions;
        this.sessionData.correct_answers += stats.correct_answers;
        this.sessionData.total_time += stats.time_taken;
        this.sessionData.last_activity = new Date().toISOString();
        
        this.updateStreak();
        this.saveToStorage();
        
        // Send to backend
        this.syncWithServer();
    }
    
    updateStreak() {
        const today = new Date().toDateString();
        const lastActivity = this.sessionData.last_activity ? 
            new Date(this.sessionData.last_activity).toDateString() : null;
        
        if (lastActivity !== today) {
            const daysDiff = this.getDaysDifference(lastActivity, today);
            
            if (daysDiff === 1) {
                this.sessionData.streak_days++;
            } else if (daysDiff > 1) {
                this.sessionData.streak_days = 1;
            }
        }
    }
    
    getDaysDifference(date1, date2) {
        if (!date1 || !date2) return 0;
        const d1 = new Date(date1);
        const d2 = new Date(date2);
        const diffTime = Math.abs(d2 - d1);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }
    
    getStats() {
        return {
            ...this.sessionData,
            accuracy: this.sessionData.questions_answered > 0 ?
                Math.round((this.sessionData.correct_answers / this.sessionData.questions_answered) * 100) : 0,
            avg_time_per_lesson: this.sessionData.lessons_completed > 0 ?
                Math.round(this.sessionData.total_time / this.sessionData.lessons_completed) : 0
        };
    }
    
    async syncWithServer() {
        try {
            await fetch('/api/sync-progress', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(this.sessionData)
            });
        } catch (error) {
            console.log('Progress sync will happen later');
        }
    }
    
    reset() {
        this.sessionData = {
            lessons_completed: 0,
            questions_answered: 0,
            correct_answers: 0,
            total_time: 0,
            streak_days: 0,
            last_activity: null
        };
        this.saveToStorage();
    }
}

// Create global progress tracker
const progressTracker = new ProgressTracker();

// Achievement system
class AchievementManager {
    constructor() {
        this.achievements = [
            {
                id: 'first_lesson',
                name: 'First Steps',
                description: 'Complete your first lesson',
                icon: '🎯',
                unlocked: false
            },
            {
                id: 'perfect_score',
                name: 'Perfect Score',
                description: 'Get 100% on a lesson',
                icon: '⭐',
                unlocked: false
            },
            {
                id: 'week_streak',
                name: 'Week Warrior',
                description: 'Maintain a 7-day streak',
                icon: '🔥',
                unlocked: false
            },
            {
                id: 'speed_demon',
                name: 'Speed Demon',
                description: 'Complete a lesson in under 10 minutes',
                icon: '⚡',
                unlocked: false
            },
            {
                id: 'century',
                name: 'Century Club',
                description: 'Answer 100 questions correctly',
                icon: '💯',
                unlocked: false
            }
        ];
        
        this.loadAchievements();
    }
    
    loadAchievements() {
        const stored = localStorage.getItem('pathlearn_achievements');
        if (stored) {
            const unlocked = JSON.parse(stored);
            this.achievements.forEach(achievement => {
                if (unlocked.includes(achievement.id)) {
                    achievement.unlocked = true;
                }
            });
        }
    }
    
    checkAchievements(stats) {
        const newAchievements = [];
        
        // First lesson
        if (stats.lessons_completed >= 1 && !this.isUnlocked('first_lesson')) {
            this.unlock('first_lesson');
            newAchievements.push(this.getAchievement('first_lesson'));
        }
        
        // Week streak
        if (stats.streak_days >= 7 && !this.isUnlocked('week_streak')) {
            this.unlock('week_streak');
            newAchievements.push(this.getAchievement('week_streak'));
        }
        
        // Century club
        if (stats.correct_answers >= 100 && !this.isUnlocked('century')) {
            this.unlock('century');
            newAchievements.push(this.getAchievement('century'));
        }
        
        // Show notifications for new achievements
        newAchievements.forEach(achievement => {
            this.showAchievementUnlock(achievement);
        });
        
        return newAchievements;
    }
    
    isUnlocked(achievementId) {
        const achievement = this.achievements.find(a => a.id === achievementId);
        return achievement ? achievement.unlocked : false;
    }
    
    unlock(achievementId) {
        const achievement = this.achievements.find(a => a.id === achievementId);
        if (achievement) {
            achievement.unlocked = true;
            this.saveAchievements();
        }
    }
    
    getAchievement(achievementId) {
        return this.achievements.find(a => a.id === achievementId);
    }
    
    saveAchievements() {
        const unlocked = this.achievements
            .filter(a => a.unlocked)
            .map(a => a.id);
        localStorage.setItem('pathlearn_achievements', JSON.stringify(unlocked));
    }
    
    showAchievementUnlock(achievement) {
        const notification = document.createElement('div');
        notification.className = 'achievement-notification';
        notification.innerHTML = `
            <div style="
                position: fixed;
                top: 100px;
                right: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 24px;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                z-index: 10000;
                animation: slideInRight 0.5s ease;
                max-width: 300px;
            ">
                <div style="font-size: 3rem; text-align: center; margin-bottom: 12px;">
                    ${achievement.icon}
                </div>
                <div style="font-weight: 700; font-size: 1.25rem; margin-bottom: 8px;">
                    Achievement Unlocked!
                </div>
                <div style="font-weight: 600; margin-bottom: 4px;">
                    ${achievement.name}
                </div>
                <div style="opacity: 0.9; font-size: 0.875rem;">
                    ${achievement.description}
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.5s ease';
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    }
}

const achievementManager = new AchievementManager();

// Export for global use
window.progressTracker = progressTracker;
window.achievementManager = achievementManager;