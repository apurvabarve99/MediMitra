from datetime import datetime, timedelta
import re
from typing import Optional, Tuple

class DateTimeParser:
    """Parse natural language dates and times"""
    
    WEEKDAYS = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    @staticmethod
    def parse_date(text: str) -> Optional[datetime.date]:
        """
        Parse natural language date input
        Supports: tomorrow, day after tomorrow, next monday, 26th Jan, 26/01, etc.
        """
        text = text.lower().strip()
        today = datetime.now().date()
        
        # Handle "today"
        if text == 'today':
            return today
        
        # Handle "tomorrow"
        if text == 'tomorrow':
            return today + timedelta(days=1)
        
        # Handle "day after tomorrow"
        if 'day after tomorrow' in text:
            return today + timedelta(days=2)
        
        # Handle "next <weekday>"
        if text.startswith('next '):
            weekday_name = text.replace('next ', '').strip()
            if weekday_name in DateTimeParser.WEEKDAYS:
                target_weekday = DateTimeParser.WEEKDAYS[weekday_name]
                current_weekday = today.weekday()
                days_ahead = (target_weekday - current_weekday + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week's same day
                return today + timedelta(days=days_ahead)
        
        # Handle specific weekday (without "next")
        for weekday_name, weekday_num in DateTimeParser.WEEKDAYS.items():
            if weekday_name in text:
                target_weekday = weekday_num
                current_weekday = today.weekday()
                days_ahead = (target_weekday - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week
                return today + timedelta(days=days_ahead)
        
        # Handle formats like "26th Jan", "26 January", "January 26"
        month_names = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'sept': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        
        # Remove ordinal suffixes (st, nd, rd, th)
        text = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', text)
        
        for month_name, month_num in month_names.items():
            if month_name in text:
                # Extract day number
                day_match = re.search(r'\b(\d{1,2})\b', text)
                if day_match:
                    day = int(day_match.group(1))
                    year = today.year
                    # If date has passed this year, use next year
                    try:
                        date = datetime(year, month_num, day).date()
                        if date < today:
                            date = datetime(year + 1, month_num, day).date()
                        return date
                    except ValueError:
                        pass
        
        # Handle DD/MM or DD/MM/YYYY format
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})/(\d{1,2})',           # DD/MM
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{1,2})-(\d{1,2})'            # DD-MM
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                day = int(groups[0])
                month = int(groups[1])
                year = int(groups[2]) if len(groups) > 2 else today.year
                
                try:
                    date = datetime(year, month, day).date()
                    if date < today and len(groups) == 2:
                        # If only DD/MM provided and date has passed, use next year
                        date = datetime(year + 1, month, day).date()
                    return date
                except ValueError:
                    pass
        
        return None
    
    @staticmethod
    def parse_time(text: str) -> Optional[datetime.time]:
        """
        Parse natural language time input
        Supports: 9am, 9:30 PM, 1530, 3pm, etc.
        """
        text = text.lower().strip()
        
        # Handle 12-hour format with AM/PM
        patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',      # 9:30 AM
            r'(\d{1,2})\s*(am|pm)',               # 9 AM
            r'(\d{1,2})\.(\d{2})\s*(am|pm)',     # 9.30 AM
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 2 and groups[1] else 0
                period = groups[-1]
                
                # Convert to 24-hour format
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                
                try:
                    return datetime.strptime(f"{hour}:{minute}", "%H:%M").time()
                except ValueError:
                    pass
        
        # Handle 24-hour format
        patterns_24h = [
            r'(\d{1,2}):(\d{2})',  # 14:30
            r'(\d{4})',             # 1430
        ]
        
        for pattern in patterns_24h:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:
                    # Format: 1430
                    hour = int(groups[0][:2])
                    minute = int(groups[0][2:])
                else:
                    # Format: 14:30
                    hour = int(groups[0])
                    minute = int(groups[1])
                
                try:
                    return datetime.strptime(f"{hour}:{minute}", "%H:%M").time()
                except ValueError:
                    pass
        
        return None
    
    @staticmethod
    def format_date_friendly(date: datetime.date) -> str:
        """Format date in a user-friendly way"""
        today = datetime.now().date()
        delta = (date - today).days
        
        if delta == 0:
            return "today"
        elif delta == 1:
            return "tomorrow"
        elif delta == 2:
            return "day after tomorrow"
        elif delta < 7:
            return date.strftime("%A")  # Weekday name
        else:
            return date.strftime("%B %d, %Y")  # Month Day, Year
    
    @staticmethod
    def format_time_friendly(time: datetime.time) -> str:
        """Format time in 12-hour format"""
        return time.strftime("%I:%M %p").lstrip('0')
