
from data_manager import load_achievements, save_achievements
from config import ACHIEVEMENTS, BADGE_LEVELS, BADGE_CATEGORIES

class AchievementSystem:
    def __init__(self):
        self.achievements = ACHIEVEMENTS
        self.badge_levels = BADGE_LEVELS
        self.badge_categories = BADGE_CATEGORIES
        self.data = load_achievements()

    def check_achievements(self, participant, points, rank, streak):
        """Checks all achievement criteria for a participant."""
        for category, achievements in self.achievements.items():
            for achievement, details in achievements.items():
                if category == 'performance' and details['criteria'](points):
                    self.award_badge(participant, category, achievement)
                elif category == 'rank' and details['criteria'](rank):
                    self.award_badge(participant, category, achievement)
                elif category == 'streak' and details['criteria'](streak):
                    self.award_badge(participant, category, achievement)

    def award_badge(self, participant, category, achievement):
        """Awards a badge to a participant and saves the data."""
        if participant not in self.data:
            self.data[participant] = {}
        if category not in self.data[participant]:
            self.data[participant][category] = {}
        if achievement not in self.data[participant][category]:
            self.data[participant][category][achievement] = 0
        
        self.data[participant][category][achievement] += 1
        save_achievements(self.data)
