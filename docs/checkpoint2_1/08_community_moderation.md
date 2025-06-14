# Community Moderation System

## Overview
This document details the implementation of a community moderation system that allows users to report problematic locations and enables administrators to review and act on these reports. The system promotes community-driven quality control.

## Why Community Moderation Was Needed

### Previous State
- No way to report problematic locations
- Inaccurate information remained uncorrected
- Spam locations persisted
- No accountability for bad data
- Admin burden to find issues manually

### Problems Solved
- **Quality Control**: Bad data could persist indefinitely
- **Safety Issues**: No way to report dangerous locations
- **Spam Prevention**: No mechanism to flag spam
- **Community Trust**: Users felt powerless against bad content
- **Admin Efficiency**: Manual searching for problems was inefficient

## Implementation Details

### LocationReport Model

```python
class LocationReport(TimestampedModel):
    """Reports submitted by users about viewing locations"""
    
    REPORT_TYPES = [
        ('DUPLICATE', 'Duplicate Location'),
        ('INACCURATE', 'Inaccurate Information'),
        ('SPAM', 'Spam or Inappropriate'),
        ('CLOSED', 'Location Closed/Inaccessible'),
        ('DANGEROUS', 'Safety Concerns'),
        ('OTHER', 'Other'),
    ]
    
    REPORT_STATUS = [
        ('PENDING', 'Pending Review'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    location = models.ForeignKey(ViewingLocation, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(help_text="Detailed description of the issue")
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='PENDING')
    
    # For duplicate reports
    duplicate_of = models.ForeignKey(ViewingLocation, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='duplicate_reports')
    
    # Review tracking
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
```

### Report Submission Endpoint

```python
@action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
def report(self, request, pk=None):
    """Submit a report about this location"""
    location = self.get_object()
    
    report_data = {
        'location': location.id,
        'report_type': request.data.get('report_type'),
        'description': request.data.get('description'),
        'duplicate_of': request.data.get('duplicate_of_id')
    }
    
    serializer = LocationReportSerializer(data=report_data)
    if serializer.is_valid():
        try:
            report = serializer.save(reported_by=request.user)
            
            # Increment report counter
            location.times_reported += 1
            location.save()
            
            return Response(LocationReportSerializer(report).data, status=201)
        except Exception as e:
            # Handle unique constraint violation
            if 'unique constraint' in str(e).lower():
                return Response({
                    'detail': 'You have already submitted this type of report for this location'
                }, status=400)
```

### Unique Constraint

```python
class Meta:
    unique_together = [['location', 'reported_by', 'report_type']]
```

This prevents users from spamming the same report type for a location.

### Admin Report Viewing

```python
@action(detail=True, methods=['GET'])
def reports(self, request, pk=None):
    """Get all reports for this location (admin only)"""
    location = self.get_object()
    
    # Only staff can see all reports
    if not request.user.is_staff:
        return Response({
            'detail': 'You do not have permission to view reports'
        }, status=403)
    
    reports = location.reports.all()
    serializer = LocationReportSerializer(reports, many=True)
    return Response(serializer.data)
```

## Usage Examples

### Submit a Report
```bash
curl -X POST http://localhost:8000/api/v1/locations/123/report/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "INACCURATE",
    "description": "The coordinates are off by about 2km. The actual location is further north."
  }'
```

### Report a Duplicate
```bash
curl -X POST http://localhost:8000/api/v1/locations/123/report/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "DUPLICATE",
    "duplicate_of_id": 456,
    "description": "This is the same location as #456 - Central Park Observatory"
  }'
```

### Report Safety Concerns
```bash
curl -X POST http://localhost:8000/api/v1/locations/789/report/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "DANGEROUS",
    "description": "Steep cliff with no barriers. Several accidents reported. Needs warning."
  }'
```

### View Reports (Admin)
```bash
curl -X GET http://localhost:8000/api/v1/locations/123/reports/ \
  -H "Authorization: Token ADMIN_TOKEN"
```

Response:
```json
[
    {
        "id": 1,
        "location": 123,
        "location_name": "Mountain Vista Point",
        "reported_by": "user456",
        "report_type": "DANGEROUS",
        "description": "Steep cliff with no barriers...",
        "status": "PENDING",
        "duplicate_of": null,
        "reviewed_by": null,
        "review_notes": "",
        "reviewed_at": null,
        "created_at": "2024-01-20T10:30:00Z"
    },
    {
        "id": 2,
        "location": 123,
        "location_name": "Mountain Vista Point",
        "reported_by": "user789",
        "report_type": "INACCURATE",
        "description": "Coordinates are wrong...",
        "status": "RESOLVED",
        "duplicate_of": null,
        "reviewed_by": "admin",
        "review_notes": "Corrected coordinates based on GPS verification",
        "reviewed_at": "2024-01-21T14:00:00Z",
        "created_at": "2024-01-20T12:00:00Z"
    }
]
```

## Report Types and Actions

### DUPLICATE
- Links to another location
- Can trigger merge process
- Helps consolidate data

### INACCURATE
- Wrong coordinates
- Incorrect information
- Outdated details

### SPAM
- Commercial spam
- Fake locations
- Inappropriate content

### CLOSED
- No longer accessible
- Permanently closed
- Access restricted

### DANGEROUS
- Safety hazards
- Requires warnings
- Urgent attention needed

### OTHER
- Catch-all category
- Requires detailed description
- Custom issues

## Moderation Workflow

### 1. User Reports Issue
- Selects report type
- Provides description
- One report per type per user

### 2. Report Queue
- Admins see pending reports
- Sorted by priority/date
- Filterable by type

### 3. Admin Review
- Investigate report
- Take appropriate action
- Update report status

### 4. Resolution
- Mark as resolved/dismissed
- Add review notes
- Notify reporter (future)

## Benefits

### For Users
- Voice concerns about locations
- Improve data quality
- Report safety issues
- Feel heard by platform

### For Administrators
- Crowdsourced quality control
- Prioritized issue queue
- Audit trail of actions
- Efficient problem resolution

### For Platform Quality
- Continuous improvement
- Community engagement
- Trust building
- Data accuracy

## Report Analytics

Track report metrics:
- Most reported locations
- Common report types
- Resolution times
- Reporter reliability

## Future Enhancements

1. **Auto-Actions**: Automatic hiding after X reports
2. **Reporter Reputation**: Weight reports by user trust
3. **Notifications**: Email alerts for urgent reports
4. **Bulk Actions**: Handle multiple reports at once
5. **Report Templates**: Pre-filled common issues
6. **Public Status**: Show report status to users
7. **Appeal Process**: Allow location owners to respond
8. **ML Detection**: Auto-detect problematic content

## Integration with Other Features

- **User Reputation**: Quality reports increase reputation
- **Location Verification**: Reports affect verification status
- **Search Ranking**: Highly reported locations rank lower
- **Map Display**: Visual indicators for reported locations
- **Duplicate Detection**: Creates duplicate reports automatically