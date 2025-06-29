
from datetime import datetime
from data_manager import load_challenges, save_challenges

class ChallengeSystem:
    def __init__(self):
        data = load_challenges()
        self.challenges = data.get('challenges', {})
        self.pending_requests = data.get('pending', {})

    def _save(self):
        """Saves the current state of challenges and pending requests."""
        save_challenges({
            'challenges': self.challenges,
            'pending': self.pending_requests
        })

    def add_challenge(self, name, description, bonus_points):
        """Adds a new challenge."""
        if name not in self.challenges:
            self.challenges[name] = {
                'name': name,
                'description': description,
                'bonus_points': bonus_points,
                'participants': [],
                'completed': []
            }
            self._save()
            return True
        return False

    def remove_challenge(self, challenge_name):
        """Removes a challenge and its pending requests."""
        if challenge_name in self.challenges:
            del self.challenges[challenge_name]
            if challenge_name in self.pending_requests:
                del self.pending_requests[challenge_name]
            self._save()
            return True
        return False

    def request_join(self, participant, challenge_name):
        """Allows a participant to request to join a challenge."""
        if challenge_name not in self.pending_requests:
            self.pending_requests[challenge_name] = []
        if participant not in self.pending_requests[challenge_name]:
            self.pending_requests[challenge_name].append(participant)
            self._save()
            return True
        return False

    def approve_request(self, participant, challenge_name, points):
        """Approves a participant's request to join a challenge."""
        if challenge_name in self.pending_requests and participant in self.pending_requests[challenge_name]:
            self.pending_requests[challenge_name].remove(participant)
            if challenge_name in self.challenges:
                self.challenges[challenge_name]['completed'].append({
                    'participant': participant,
                    'points': points,
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            self._save()
            return True
        return False

    def reject_request(self, participant, challenge_name):
        """Rejects a participant's request to join a challenge."""
        if challenge_name in self.pending_requests and participant in self.pending_requests[challenge_name]:
            self.pending_requests[challenge_name].remove(participant)
            self._save()
            return True
        return False
