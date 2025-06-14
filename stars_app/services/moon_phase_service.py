class MoonPhaseService:
    """Service for handling moon phase calculations and descriptions"""

    @staticmethod
    def get_moon_phase_name(moon_phase_percentage):
        """
        Converts moon phase percentage (0-100) to descriptive phase names.
        
        The lunar cycle is typically divided into 8 main phases:
        - New Moon (0%)
        - Waxing Crescent (1-24%)
        - First Quarter (25-49%)
        - Waxing Gibbous (50-74%)
        - Full Moon (75-100%)
        - Waning Gibbous (74-50%)
        - Last Quarter (49-25%)
        - Waning Crescent (24-1%)
        
        Returns both a short and detailed description of the phase.
        """
        if moon_phase_percentage is None:
            return {
                'short_name': 'Unknown',
                'description': 'Moon phase data not available'
            }
        
        # Normalize the percentage to handle any input
        phase = moon_phase_percentage % 100
        
        # Define phase ranges and their descriptions
        if phase == 0 or phase == 100:
            return {
                'short_name': 'New Moon',
                'description': 'The Moon is not visible from Earth'
            }
        elif 0 < phase <= 24:
            return {
                'short_name': 'Waxing Crescent',
                'description': 'Less than half of the Moon is illuminated and increasing'
            }
        elif 24 < phase <= 49:
            return {
                'short_name': 'First Quarter',
                'description': 'Half of the Moon is illuminated and increasing'
            }
        elif 49 < phase <= 74:
            return {
                'short_name': 'Waxing Gibbous',
                'description': 'More than half of the Moon is illuminated and increasing'
            }
        elif 74 < phase <= 100:
            return {
                'short_name': 'Full Moon',
                'description': 'The entire Moon is illuminated'
            }
        elif 74 < phase <= 99:
            return {
                'short_name': 'Waning Gibbous',
                'description': 'More than half of the Moon is illuminated and decreasing'
            }
        elif 49 < phase <= 74:
            return {
                'short_name': 'Last Quarter',
                'description': 'Half of the Moon is illuminated and decreasing'
            }
        else:
            return {
                'short_name': 'Waning Crescent',
                'description': 'Less than half of the Moon is illuminated and decreasing'
            }