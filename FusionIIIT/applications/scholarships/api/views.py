from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from applications.scholarships.models import Previous_winner, Award_and_scholarship,Mcm,Director_gold,Notional_prize,Director_silver,Proficiency_dm,Release,SingleParent
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import DirectorSilverDecisionSerializer, DMProficiencyDecisionSerializer
from rest_framework import status
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)
from rest_framework import viewsets
from applications.scholarships.api.serializers import PreviousWinnerSerializer,AwardAndScholarshipSerializer,McmSerializer,NotionalPrizeSerializer,DirectorGoldSerializer,DirectorSilverSerializer,ProficiencyDmSerializer,ReleaseSerializer,McmStatusUpdateSerializer,SingleParentSerializer,SingleParentStatusUpdateSerializer
from django.shortcuts import get_object_or_404
import datetime
from .pdf_generator import generate_mcm_pdf

# ====== UTILITY FUNCTIONS ======

def check_scholarship_deadline(award_name):
    """
    Check if a scholarship's application deadline has passed.
    
    Args:
        award_name (str): Name of the scholarship/award
        
    Returns:
        tuple: (is_open, message)
            - is_open (bool): True if application window is open
            - message (str): Descriptive message about deadline status
    """
    current_date = datetime.date.today()
    
    try:
        # Get all releases for this award
        releases = Release.objects.filter(award__icontains=award_name)
        
        if not releases.exists():
            return False, f"No release found for {award_name}"
        
        # Check if any release has an open application window
        for release in releases:
            if release.startdate <= current_date <= release.enddate:
                days_remaining = (release.enddate - current_date).days
                return True, f"Application window open. Deadline: {release.enddate} ({days_remaining} days remaining)"
        
        # If no open window found, deadline has passed
        latest_release = releases.order_by('-enddate').first()
        return False, f"Application deadline has passed. Last deadline was {latest_release.enddate}."
        
    except Exception as e:
        print(f"Error checking scholarship deadline for {award_name}: {e}")
        # Return error but don't block submission in case of exception
        return False, f"Error checking deadline: {str(e)}"


def validate_scholarship_deadline(award_name, raise_error=True):
    """
    Validate and raise error if scholarship deadline has passed.
    
    Args:
        award_name (str): Name of the scholarship/award
        raise_error (bool): If True, raises error response; if False, returns tuple
        
    Returns:
        If raise_error=False: tuple (is_open, message)
        If raise_error=True: raises Response error or None if valid
    """
    is_open, message = check_scholarship_deadline(award_name)
    
    if not is_open:
        if raise_error:
            raise ValueError(f"Deadline validation failed: {message}")
        return False, message
    
    if raise_error:
        return None
    return True, message

# ====== END UTILITY FUNCTIONS ======

#This api is for invite application 
class ReleaseCreateView(APIView):
    def post(self, request):
        serializer = ReleaseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the data to the database
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckApplicationWindowView(APIView):
    def post(self, request):
        award_name = request.data.get('award')
        current_date = datetime.date.today()

        if not award_name:
            return Response({'result': 'Failure', 'error': 'Award is a required field'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            #Get all the rows with the award name
            releases = Release.objects.filter(award=award_name)
        except Release.DoesNotExist:
            return Response({'result': 'Failure', 'message': 'No release found for the specified award'}, status=status.HTTP_200_OK)
        for release in releases:
            # Check if the current date is within the start and end dates of the release
            if release.startdate <= current_date <= release.enddate:
                return Response({'result': 'Success', 'message': 'Application window is open.'}, status=status.HTTP_200_OK)
            
        # If the current date is outside the start and end dates
        return Response({'result': 'Failure', 'message': 'Application window is closed.'}, status=status.HTTP_200_OK)


class GetActiveScholarshipsView(APIView):
    """
    API endpoint to fetch only scholarships/awards with active application deadlines.
    Returns scholarships where today's date is between startdate and enddate.
    """
    def get(self, request):
        current_date = datetime.date.today()
        
        try:
            # Get all releases with active deadlines (today is between startdate and enddate)
            active_releases = Release.objects.filter(
                startdate__lte=current_date,
                enddate__gte=current_date
            ).distinct('award').values('award', 'id', 'startdate', 'enddate', 'programme', 'batch')
            
            scholarships = []
            for release in active_releases:
                scholarships.append({
                    'award_name': release['award'],
                    'release_id': release['id'],
                    'startdate': release['startdate'],
                    'enddate': release['enddate'],
                    'programme': release['programme'],
                    'batch': release['batch'],
                    'days_remaining': (release['enddate'] - current_date).days
                })
            
            if scholarships:
                return Response({
                    'result': 'Success',
                    'count': len(scholarships),
                    'scholarships': scholarships,
                    'message': f'{len(scholarships)} active scholarship(s) available for application'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'result': 'Failure',
                    'count': 0,
                    'scholarships': [],
                    'message': 'No active scholarships available at the moment. Please check back later.'
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'result': 'Failure',
                'error': str(e),
                'message': 'Error fetching active scholarships'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetScholarshipDeadlineView(APIView):
    """
    API endpoint to check if a specific scholarship's deadline has passed.
    Returns deadline info and whether application is currently open.
    """
    def post(self, request):
        award_name = request.data.get('award')
        current_date = datetime.date.today()
        
        if not award_name:
            return Response({
                'result': 'Failure',
                'error': 'Award name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the most recent release for this award
            release = Release.objects.filter(award=award_name).order_by('-enddate').first()
            
            if not release:
                return Response({
                    'result': 'Failure',
                    'error': f'No scholarship found with name: {award_name}'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if application window is open
            is_open = release.startdate <= current_date <= release.enddate
            days_remaining = (release.enddate - current_date).days
            
            return Response({
                'result': 'Success',
                'award_name': award_name,
                'is_open': is_open,
                'startdate': release.startdate,
                'enddate': release.enddate,
                'days_remaining': days_remaining if is_open else 0,
                'status': 'Open' if is_open else ('Closed' if current_date > release.enddate else 'Not Started'),
                'message': (
                    f'Application deadline: {release.enddate}. '
                    f'{days_remaining} days remaining.' if is_open
                    else f'Application window closed on {release.enddate}.'
                )
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'result': 'Failure',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#This API is for editing the catalogue by convenor and assistant and saving in the database
class AwardAndScholarshipCreateView(APIView):
    def post(self, request, pk=None):
        # Check if pk is provided, if yes, try to update the existing entry
        pk=request.data.get("id")
        if pk is not None:
            award = get_object_or_404(Award_and_scholarship, pk=pk)
            # Update the existing entry
            serializer = AwardAndScholarshipSerializer(award, data=request.data, partial=True)
        else:
            # If pk is not provided, create a new entry
            serializer = AwardAndScholarshipSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # 201 Created response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # 400 Bad Request if data is invalid

#This api for fetching the award and scholarship catalogue from the database
class create_award(APIView):

    def get(self, request, *args, **kwargs):
        awards = Award_and_scholarship.objects.all()  # Fetch all awards
        serializer = AwardAndScholarshipSerializer(awards, many=True)  # Serialize the awards
        return Response(serializer.data, status=status.HTTP_200_OK)  

#This api is for Previous Winner 
class GetWinnersView(APIView):

    def post(self, request, *args, **kwargs):
        award_id = request.data.get('award_id')
        batch_year = int(request.data.get('batch'))
        programme_name = request.data.get('programme')

        try:
            award = Award_and_scholarship.objects.get(id=award_id)
        except Award_and_scholarship.DoesNotExist:
            return Response({'result': 'Failure', 'error': 'Award not found'}, status=status.HTTP_404_NOT_FOUND)

        winners = Previous_winner.objects.select_related('student', 'award_id').filter(
            year=batch_year, award_id=award, programme=programme_name
        )
        
        context = {
            'student_name': [],
            'student_program': [],
            'roll': []
        }

        if winners.exists():
            for winner in winners:
                extra_info = ExtraInfo.objects.get(id=winner.student_id)
                student_id = Student.objects.get(id=extra_info)
                student_name = extra_info.user.first_name
                student_roll = winner.student_id
                student_program = student_id.programme

                context['student_name'].append(student_name)
                context['roll'].append(student_roll)
                context['student_program'].append(student_program)
                print(student_roll)

            context['result'] = 'Success'
            return Response(context, status=status.HTTP_200_OK)

        else:
            return Response({'result': 'Failure', 'error': 'No winners found'}, status=status.HTTP_404_NOT_FOUND)

class McmUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        
        # Check deadline using utility function
        try:
            is_open, deadline_message = check_scholarship_deadline("Merit-cum-Means Scholarship")
            if not is_open:
                return Response({
                    'result': 'Failure',
                    'error': 'Application deadline has passed.',
                    'message': deadline_message
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error checking MCM deadline: {e}")
            # Don't block submission if there's an error checking deadline
            pass
        
        # Prevent Duplicate submission
        from applications.scholarships.models import Mcm
        active_mcm = Mcm.objects.filter(student=request.user.username).exclude(status__in=['REJECT', 'Reject', 'ACCEPTED', 'APPROVED', 'Complete', 'COMPLETE', 'NEEDS_INFO', 'WITHDRAWN']).exists()
        if active_mcm:
            return Response({'error': 'You already have an active MCM Scholarship application under review. You cannot apply again until it is accepted or rejected.'}, status=status.HTTP_400_BAD_REQUEST)
        
        needs_info_mcm = Mcm.objects.filter(student=request.user.username, status='NEEDS_INFO').first()

        if request.data.get('is_resubmit') == 'true':
            if not needs_info_mcm:
                return Response({'error': 'No NEEDS_INFO application found to resubmit.'}, status=status.HTTP_400_BAD_REQUEST)
            request.data['status'] = 'SUBMITTED'
            serializer = McmSerializer(needs_info_mcm, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Resubmitted successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        required_fields = [
            'email', 'student_name', 'roll_no', 'batch', 'programme',
            'category', 'mobile_number', 'address', 'annual_income', 'cpi'
        ]

        required_files = [
            'undertaking_form', 'application_form', 'last_sem_result'
        ]

        batch = request.data.get('batch', '')
        if batch == '2025':
            required_fields.append('jee_rank')
            required_files.append('score_card')

        parent_status = request.data.get('parent_status', 'Both Parents Alive')
        
        if parent_status == 'Both Parents Alive':
            required_fields.extend(['father_name', 'mother_name'])
            required_files.extend(['income_certificate', 'mother_income_certificate'])
        elif parent_status == 'Single Parent (Father Alive)':
            required_fields.append('father_name')
            required_files.extend(['income_certificate', 'death_certificate'])
        elif parent_status == 'Single Parent (Mother Alive)':
            required_fields.append('mother_name')
            required_files.extend(['mother_income_certificate', 'death_certificate'])
        elif parent_status == 'Orphan / No Parents Alive':
            required_fields.append('father_name')
            required_files.extend(['income_certificate', 'death_certificate'])

        category = request.data.get('category', 'GEN')
        if category and category != 'GEN':
            required_files.append('caste_certificate')
            
        for field in required_fields:
            if not request.data.get(field):
                return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)
                
        for file in required_files:
            if not request.FILES.get(file) and not request.data.get(file):
                # sometimes files are passed in request.data in some setups, but typically request.FILES
                return Response({'error': f'{file} is required'}, status=status.HTTP_400_BAD_REQUEST)

        request.data['student'] = request.user.username
        
        # Default required fields in Mcm model not captured by forms anymore
        defaults = {
            'brother_name': 'NA', 'sister_name': 'NA',
            'income_father': 0, 'income_mother': 0, 'income_other': 0,
            'father_occ': 'public', 'mother_occ': 'HOUSE_WIFE',
            'house': 'NA', 'father_occ_desc': 'NA', 'mother_occ_desc': 'NA',
            'four_wheeler': 0, 'four_wheeler_desc': 'NA',
            'two_wheeler': 0, 'two_wheeler_desc': 'NA',
            'plot_area': 0, 'constructed_area': 0,
            'school_fee': 0, 'school_name': 'NA',
            'bank_name': 'NA', 'loan_amount': 0,
            'college_fee': 0, 'college_name': 'NA',
            'status': 'SUBMITTED', 'brother_occupation': 'NA', 'sister_occupation': 'NA'
        }
        for k, v in defaults.items():
            if not request.data.get(k):
                request.data[k] = v

        if not request.data.get('award_id'):
            from applications.scholarships.models import Award_and_scholarship
            award_obj = Award_and_scholarship.objects.filter(award_name__icontains='MCM').first()
            if award_obj:
                request.data['award_id'] = award_obj.id
            else:
                request.data['award_id'] = 1

        try:
            if needs_info_mcm:
                serializer = McmSerializer(needs_info_mcm, data=request.data)
            else:
                serializer = McmSerializer(data=request.data)
            if serializer.is_valid():
                mcm_instance = serializer.save()
                pdf_file = generate_mcm_pdf(mcm_instance)
                mcm_instance.generated_pdf.save(pdf_file.name, pdf_file)
                mcm_instance.save()
                return Response(McmSerializer(mcm_instance).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e), "traceback": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SingleParentUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Checking deadline
        try:
            import json
            import os
            from datetime import datetime
            from rest_framework.response import Response
            from rest_framework import status
            catalog_file = os.path.join(os.path.dirname(__file__), 'frontend_catalog.json')
            if os.path.exists(catalog_file):
                with open(catalog_file, 'r') as f:
                    catalog = json.load(f)
                    for item in catalog:
                        name = item.get('name', '').lower()
                        if 'single' in name:
                            deadline_str = item.get('deadline')
                            if deadline_str:
                                deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                                if datetime.now().date() > deadline_date:
                                    return Response({'error': 'Application deadline has passed.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Error parsing deadline:", e)

        # Checking deadline
        try:
            import json
            import os
            from datetime import datetime
            from rest_framework.response import Response
            from rest_framework import status
            catalog_file = os.path.join(os.path.dirname(__file__), 'frontend_catalog.json')
            if os.path.exists(catalog_file):
                with open(catalog_file, 'r') as f:
                    catalog = json.load(f)
                    for item in catalog:
                        name = item.get('name', '').lower()
                        if 'single' in name:
                            deadline_str = item.get('deadline')
                            if deadline_str:
                                deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                                if datetime.now().date() > deadline_date:
                                    return Response({'error': 'Application deadline has passed.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Error parsing deadline:", e)

        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        # Prevent Duplicate submission
        from applications.scholarships.models import SingleParent
        active_sp = SingleParent.objects.filter(student=request.user.username).exclude(status__in=['REJECT', 'Reject', 'ACCEPTED', 'APPROVED', 'Complete', 'COMPLETE', 'NEEDS_INFO', 'WITHDRAWN']).exists()
        if active_sp:
            return Response({'error': 'You already have an active Single Parent Scholarship application under review. You cannot apply again until it is accepted or rejected.'}, status=status.HTTP_400_BAD_REQUEST)

        needs_info_sp = SingleParent.objects.filter(student=request.user.username, status='NEEDS_INFO').first()

        if request.data.get('is_resubmit') == 'true':
            if not needs_info_sp:
                return Response({'error': 'No NEEDS_INFO application found to resubmit.'}, status=status.HTTP_400_BAD_REQUEST)
            request.data['status'] = 'SUBMITTED'
            serializer = SingleParentSerializer(needs_info_sp, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Resubmitted successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        request.data['student'] = request.user.username

        # We map frontend mcm-style form to single-parent model here
        from applications.scholarships.models import Award_and_scholarship
        
        # Determine parent_type and parent_name based on parent_status
        parent_status = request.data.get('parent_status', '')
        if parent_status == 'Single Parent (Father Alive)':
            request.data['parent_type'] = 'FATHER'
            request.data['parent_name'] = request.data.get('father_name', '')
        elif parent_status == 'Single Parent (Mother Alive)':
            request.data['parent_type'] = 'MOTHER'
            request.data['parent_name'] = request.data.get('mother_name', '')
        elif parent_status == 'Orphan / No Parents Alive':
            request.data['parent_type'] = 'GUARDIAN'
            request.data['parent_name'] = request.data.get('guardian_name', '')
        else:
            request.data['parent_type'] = 'FATHER'
            request.data['parent_name'] = request.data.get('father_name', '')

        # Fallback values
        request.data['parent_occupation'] = request.data.get('parent_occupation', 'Not Provided')
        if request.FILES.get('mother_income_certificate') and not request.FILES.get('income_certificate'):
            request.data['income_certificate'] = request.FILES.get('mother_income_certificate')
        
        
        # award_id mapping if not provided
        if not request.data.get('award_id'):
            award_obj = Award_and_scholarship.objects.filter(award_name__icontains='Single').first()
            if award_obj:
                request.data['award_id'] = award_obj.id
            else:
                request.data['award_id'] = 1

        try:
            if needs_info_sp:
                serializer = SingleParentSerializer(needs_info_sp, data=request.data)
            else:
                serializer = SingleParentSerializer(data=request.data)
            if serializer.is_valid():
                instance = serializer.save()
                return Response(SingleParentSerializer(instance).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e), "traceback": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SingleParentRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        data = SingleParent.objects.filter(student=roll_number)
        
        if not data.exists():
            return Response([], status=status.HTTP_200_OK)
        
        serializer = SingleParentSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class McmRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        mcm_data = Mcm.objects.filter(student=roll_number)
        
        if not mcm_data.exists():
            return Response([], status=status.HTTP_200_OK)
        
        serializer = McmSerializer(mcm_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class DirectorSilverRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        director_silver_data = Director_silver.objects.filter(student=roll_number)
        
        if not director_silver_data.exists():
            return Response({"detail": "No Director Silver data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DirectorSilverSerializer(director_silver_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class DirectorSilverUpdateView(APIView):
    def post(self, request):
        # Check deadline for Director's Silver Medal
        try:
            is_open, deadline_message = check_scholarship_deadline("Director's Silver Medal")
            if not is_open:
                return Response({
                    'result': 'Failure',
                    'error': 'Application deadline has passed.',
                    'message': deadline_message
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error checking Director's Silver deadline: {e}")
            pass
        
        request.data['student']=request.user.username
        request.data['date']= datetime.date.today()
        serializer = DirectorSilverSerializer(data=request.data)
        if serializer.is_valid():
            director_silver_instance = serializer.save()
            return Response(DirectorSilverSerializer(director_silver_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class DirectorGoldRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        director_gold_data = Director_gold.objects.filter(student=roll_number)
        
        if not director_gold_data.exists():
            return Response({"detail": "No Director Gold data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DirectorGoldSerializer(director_gold_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class DirectorGoldUpdateView(APIView):
    def post(self, request):
        # Check deadline for Director's Gold Medal
        try:
            is_open, deadline_message = check_scholarship_deadline("Director's Gold Medal")
            if not is_open:
                return Response({
                    'result': 'Failure',
                    'error': 'Application deadline has passed.',
                    'message': deadline_message
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error checking Director's Gold deadline: {e}")
            pass
        
        request.data['student']=request.user.username
        serializer = DirectorGoldSerializer(data=request.data)
        if serializer.is_valid():
            director_gold_instance = serializer.save()
            return Response(DirectorGoldSerializer(director_gold_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProficiencyDmUpdateView(APIView):
    def post(self, request):
        # Check deadline for D&M Proficiency Gold Medal
        try:
            is_open, deadline_message = check_scholarship_deadline("D&M Proficiency Gold Medal")
            if not is_open:
                return Response({
                    'result': 'Failure',
                    'error': 'Application deadline has passed.',
                    'message': deadline_message
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error checking D&M Proficiency deadline: {e}")
            pass
        
        request.data['student']=request.user.username
        print(request.data)
        serializer = ProficiencyDmSerializer(data=request.data)
        if serializer.is_valid():
            proficiency_dm_instance = serializer.save()
            return Response(ProficiencyDmSerializer(proficiency_dm_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProficiencyDmRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        proficiency_dm_data = Proficiency_dm.objects.filter(student=roll_number)
        
        if not proficiency_dm_data.exists():
            return Response({"detail": "No Proficiency DM data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProficiencyDmSerializer(proficiency_dm_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

#This api for showing the list of student who has applied for mcm scholarship to convenor assistant 
class ScholarshipDetailView(APIView):
    def get(self, request):
        # Fetch all records from the Mcm table
        mcm_data = Mcm.objects.all()
        sp_data = SingleParent.objects.all()
        # Serialize the data
        mcm_serializer = McmSerializer(mcm_data, many=True)
        sp_serializer = SingleParentSerializer(sp_data, many=True)
        
        mcm_list = list(mcm_serializer.data)
        sp_list = list(sp_serializer.data)
        
        for item in sp_list:
            item['scholarship_type'] = 'Single Parent'
            item['name'] = 'Single Parent Scholarship'
        for item in mcm_list:
            item['scholarship_type'] = 'Merit Cum Means (MCM)'
            item['name'] = 'Merit Cum Means (MCM)'
            
        combined_data = mcm_list + sp_list
        
        return Response(combined_data, status=status.HTTP_200_OK)

class DirectorGoldListView(APIView):
    def get(self, request):
        # Fetch all entries
        director_gold_entries = Director_gold.objects.all()  
        # Serialize all entries
        serializer = DirectorGoldSerializer(director_gold_entries, many=True)  
        # Return the serialized data as a response
        return Response(serializer.data, status=status.HTTP_200_OK)

class DMProficiencyListView(APIView):
    def get(self, request):
        # Fetch all entries
        proficiency_dm_entries = Proficiency_dm.objects.all()
        # Serialize all entries
        serializer = ProficiencyDmSerializer(proficiency_dm_entries, many=True)
        # Return the serialized data as a response
        return Response(serializer.data, status=status.HTTP_200_OK)

#This api is for showing the all the documnet to the convenor or assistant submitted by the student in browse application 
class StudentDetailView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mcm_entry = Mcm.objects.get(student_id=student_id)
        except Mcm.DoesNotExist:
            return Response({"error": "No record found for the given student ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = McmSerializer(mcm_entry)
        return Response(serializer.data, status=status.HTTP_200_OK)

#This api is for showing the list of student who has applied for director silver in browse application in convenor and assistant
class DirectorSilverDetailView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        
        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            director_silver_entry = Director_silver.objects.get(student__id=student_id)
        except Director_silver.DoesNotExist:
            return Response({"error": "No record found for the given student ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DirectorSilverSerializer(director_silver_entry)
        return Response(serializer.data, status=status.HTTP_200_OK)

#This api is for showing the list of student who has applied for director gold in browse application in convenor and assistant
class DirectorGoldDetailView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')

        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            director_gold_entry = Director_gold.objects.get(student__id=student_id)
        except Director_gold.DoesNotExist:
            return Response({"error": "No record found for the given student ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DirectorGoldSerializer(director_gold_entry)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetReleaseByAwardView(APIView):
    def post(self, request, *args, **kwargs):
        # Get the award name from the request
        award_name = request.data.get('award')

        # Check if the award variable is provided
        if not award_name:
            return Response(
                {'result': 'Failure', 'error': 'Award is a required field'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch records from the Release table where the award matches
        releases = Release.objects.filter(award=award_name)

        # Check if any records were found
        if releases.exists():
            # Build the response data
            data = []
            for release in releases:
                data.append({
                    'id': release.id,
                    'date_time': release.date_time,
                    'programme': release.programme,
                    'startdate': release.startdate,
                    'enddate': release.enddate,
                    'award': release.award,
                    'remarks': release.remarks,
                    'batch': release.batch,
                    'notif_visible': release.notif_visible,
                })

            return Response({'result': 'Success', 'data': data}, status=status.HTTP_200_OK)

        # If no records found
        return Response(
            {'result': 'Failure', 'error': 'No releases found for the specified award'},
            status=status.HTTP_404_NOT_FOUND
        )

#This api for MCM status that is accept, reject and under review
class McmStatusUpdateView(APIView):
    def post(self, request):
        # Fetch the Mcm instance based on the provided primary key (pk)
        mcm_instance = get_object_or_404(Mcm,id=request.data.get('id'))
        
        # Deserialize the input data with the existing object
        serializer = McmStatusUpdateSerializer(mcm_instance, data=request.data, partial=True)
        
        # Validate the data
        if serializer.is_valid():
            # Save the updated status
            serializer.save()
            return Response({"message": "Status updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        
        # Return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SingleParentStatusUpdateView(APIView):
    def post(self, request):
        sp_instance = get_object_or_404(SingleParent,id=request.data.get('id'))
        serializer = SingleParentStatusUpdateSerializer(sp_instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Status updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#This api for Director silver accepting and rejecting the application by convenor and assistant
class DirectorSilverDecisionView(APIView):
    def post(self, request):
        # Deserialize the request data
        serializer = DirectorSilverDecisionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Retrieve the Director_silver instance using the provided id
                director_silver = Director_silver.objects.get(id=request.data['id'])
                
                # Update the status field
                director_silver.status = serializer.validated_data['status']
                director_silver.save()

                return Response({"message": f"Application has been {director_silver.status.lower()}."},
                                status=status.HTTP_200_OK)

            except Director_silver.DoesNotExist:
                return Response({"error": "Director_silver entry not found."},
                                status=status.HTTP_404_NOT_FOUND)
        
        # If the data is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DMProficiencyDecisionView(APIView):
    def post(self, request):
        # Deserialize the request data
        serializer = DMProficiencyDecisionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Retrieve the Proficiency_dm instance using the provided id
                proficiency_dm = Proficiency_dm.objects.get(id=request.data['id'])
                
                # Update the status field
                proficiency_dm.status = serializer.validated_data['status']
                proficiency_dm.save()

                return Response({"message": f"Application has been {proficiency_dm.status.lower()}."},
                                status=status.HTTP_200_OK)

            except Proficiency_dm.DoesNotExist:
                return Response({"error": "Proficiency_dm entry not found."},
                                status=status.HTTP_404_NOT_FOUND)
        
        # If the data is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

##This api for Director gold accepting and rejecting the application by convenor and assistant
class DirectorGoldAcceptRejectView(APIView):
    def post(self, request):
        # Get the ID of the Director_gold entry to update
        director_gold_id = request.data.get('id')
        action = request.data.get('action')  # 'accept' or 'reject'
        
        # Check if the action is valid
        if action not in ['accept', 'reject']:
            return Response({'error': 'Invalid action. Please choose either "accept" or "reject".'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the Director_gold entry from the database using the ID
            director_gold = Director_gold.objects.get(id=director_gold_id)
        except Director_gold.DoesNotExist:
            return Response({'error': 'Director_gold entry not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Update the status based on the action
        if action == 'accept':
            director_gold.status = 'ACCEPTED'
        else:
            director_gold.status = 'REJECTED'

        # Save the updated Director_gold entry
        director_gold.save()

        # Return the updated entry as a response
        serializer = DirectorGoldSerializer(director_gold)
        return Response(serializer.data, status=status.HTTP_200_OK)

#API View to list all entries of the Director_silver model.
class DirectorSilverListView(APIView):
    """
    API View to list all entries of the Director_silver model.
    """
    def get(self, request):
        director_silver_entries = Director_silver.objects.all()
        serializer = DirectorSilverSerializer(director_silver_entries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class McmDocumentsRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roll_number = request.data.get("roll")  # Roll number from request body

        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)

        mcm_instance = get_object_or_404(Mcm, student__id=roll_number)

        documents = {
            "income_certificate": bytes(mcm_instance.income_certificate).decode('utf-8') if mcm_instance.income_certificate else None,
            "marksheet": bytes(mcm_instance.Marksheet).decode('utf-8') if mcm_instance.Marksheet else None,
            "bank_details": bytes(mcm_instance.Bank_details).decode('utf-8') if mcm_instance.Bank_details else None,
            "affidavit": bytes(mcm_instance.Affidavit).decode('utf-8') if mcm_instance.Affidavit else None,
            "aadhar_card": bytes(mcm_instance.Aadhar_card).decode('utf-8') if mcm_instance.Aadhar_card else None,
            "fee_receipt": bytes(mcm_instance.Fee_Receipt).decode('utf-8') if mcm_instance.Fee_Receipt else None,
        }

        return Response(documents, status=status.HTTP_200_OK)

class DirectorSilverMarksheetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roll_number = request.data.get('roll')  # Get roll number from POST request body
        
        if not roll_number:
            return Response({"error": "Roll number is required"}, status=400)
        
        director_silver_entry = get_object_or_404(Director_silver, student_id=roll_number)

        marksheet_data = director_silver_entry.Marksheet  
        if marksheet_data:
            marksheet_str = bytes(marksheet_data).decode('utf-8')  # Convert memoryview to bytes first, then decode
        else:
            marksheet_str = None

        return Response({
            "marksheet": marksheet_str,
        })

class DirectorGoldMarksheetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roll_number = request.data.get("roll")  # Get roll number from POST request body

        if not roll_number:
            return Response({"error": "Roll number is required"}, status=400)

        record = get_object_or_404(Director_gold, student_id=roll_number)

        marksheet_data = record.Marksheet  
        if marksheet_data:
            marksheet_str = bytes(marksheet_data).decode('utf-8')  # Convert memoryview to bytes first, then decode
        else:
            marksheet_str = None

        return Response({
            "marksheet": marksheet_str,
        }, status=200)

class WithdrawApplicationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        try:
            scholarship_type = request.data.get('scholarship_type', '')
            if 'single' in scholarship_type.lower():
                application = SingleParent.objects.get(id=pk)
            else:
                application = Mcm.objects.get(id=pk)
            
            # Application Ownership Check
            user = request.user
            if hasattr(application, 'student') and application.student.id.user != user:
                return Response({'error': 'You do not have permission to withdraw this application.'}, status=status.HTTP_403_FORBIDDEN)
            
            # Check Status
            eligible_statuses = ['SUBMITTED', 'UNDER_REVIEW', 'PENDING', 'INCOMPLETE', 'NEEDS_INFO']
            
            # Some applications use lowercase/mixed. 
            current_status = application.status.upper() if application.status else ''
            
            if current_status in eligible_statuses or not current_status:
                application.status = 'WITHDRAWN' # Ensure it does not clash
                application.save()
                
                # Notify SPACS Assistant
                try:
                    from applications.scholarships.models import Notification
                    Notification.objects.create(
                        student_id=application.student.id.id,
                        notification=f"{user.username} has withdrawn their application for {application.scholarship_type}.",
                    )
                except Exception as e:
                    pass
                
                return Response({'message': 'Application withdrawn successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Cannot withdraw after forwarding or approval.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
