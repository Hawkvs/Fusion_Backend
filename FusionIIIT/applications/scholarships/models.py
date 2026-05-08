import datetime
from django.db import models
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo

class Constants:
    STATUS_CHOICES = (
        ('Complete', 'COMPLETE'),
        ('Incomplete', 'INCOMPLETE'),
        ('Reject', 'REJECT'),
        ('Accept', 'ACCEPT'),
        ('ACCEPT', 'Accept'),
        ('REJECT', 'Reject'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('UNDER_REVIEW', 'Under Review'),
        ('SUBMITTED', 'Submitted'),
        ('FORWARDED', 'Forwarded'),
        ('NEEDS_INFO', 'Needs Info'),
        ('APPROVED', 'Approved')
    )
    PARENT_STATUS_CHOICES = (
        ('Both Parents Alive', 'Both Parents Alive'),
        ('Single Parent', 'Single Parent')
    )
    SINGLE_PARENT_CHOICES = (
        ('FATHER', 'FATHER'),
        ('MOTHER', 'MOTHER')
    )
    TIME = (
        ('0', '12 Midnight'),
        ('1am', '1'),
        ('2am', '2'),
        ('3am', '3'),
        ('4am', '4'),
        ('5am', '5'),
        ('6am', '6'),
        ('7am', '7'),
        ('8am', '8'),
        ('9am', '9'),
        ('10am', '10'),
        ('11am', '11'),
        ('12 Noon', '12'),
        ('1pm', '13'),
        ('2pm', '14'),
        ('3pm', '15'),
        ('4pm', '16'),
        ('5pm', '17'),
        ('6pm', '18'),
        ('7pm', '19'),
        ('8pm', '20'),
        ('9pm', '21'),
        ('10pm', '22'),
        ('11pm', '23'),
        ('12 Midnight', '0')
    )
    BATCH = (
        ('UG1', 'UG1'),
        ('UG2', 'UG2'),
        ('UG3', 'UG3'),
        ('UG4', 'UG4'),
        ('PG1', 'PG1'),
        ('PG2', 'PG2')
    )
    FATHER_OCC_CHOICE = (
        ('government', 'Government'),
        ('private', 'Private'),
        ('public', 'Public'),
        ('business', 'Business'),
        ('medical', 'Medical'),
        ('consultant', 'Consultant'),
        ('pensioners', 'Pensioners')
    )
    MOTHER_OCC_CHOICES = (
        ('EMPLOYED', 'EMPLOYED'),
        ('HOUSE_WIFE', 'HOUSE_WIFE')
    )
    HOUSE_TYPE_CHOICES = (
        ('RENTED', 'RENTED'),
        ('OWNED', 'OWNED')
    )

class Award_and_scholarship(models.Model):
    award_name = models.CharField(max_length=100, default='')
    catalog = models.TextField(max_length=5000)

    class Meta:
        db_table = 'Award_and_scholarship'

    def __str__(self):
        return self.award_name

class Mcm(models.Model):
    brother_name = models.CharField(max_length=30, null=True)
    brother_occupation = models.TextField(max_length=100, null=True)
    sister_name = models.CharField(max_length=30, null=True)
    sister_occupation = models.TextField(max_length=100, null=True)
    
    # New fields added as per requirements
    email = models.EmailField(max_length=255, null=True, blank=True)
    jee_rank = models.CharField(max_length=50, null=True, blank=True)
    student_name = models.CharField(max_length=100, null=True, blank=True)
    roll_no = models.CharField(max_length=50, null=True, blank=True)
    batch = models.CharField(max_length=50, null=True, blank=True)
    programme = models.CharField(max_length=50, null=True, blank=True)
    cpi = models.FloatField(null=True, blank=True)
    last_sem_result = models.FileField(upload_to='scholarships/mcm/last_sem_result/', null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    
    income_father = models.IntegerField(default=0)
    income_mother = models.IntegerField(default=0)
    income_other = models.IntegerField(default=0)
    father_occ = models.CharField(max_length=10,
                                  choices=Constants.FATHER_OCC_CHOICE,
                                  default='')
    mother_occ = models.CharField(max_length=10,
                                  choices=Constants.MOTHER_OCC_CHOICES,
                                  default='')
    father_occ_desc = models.CharField(max_length=30, null=True)
    mother_occ_desc = models.CharField(max_length=30, null=True)
    four_wheeler = models.IntegerField(blank=True, null=True)
    four_wheeler_desc = models.CharField(max_length=30, null=True)
    two_wheeler = models.IntegerField(blank=True, null=True)
    two_wheeler_desc = models.CharField(max_length=30, null=True)
    house = models.CharField(max_length=10, null=True)
    plot_area = models.IntegerField(blank=True, null=True)
    constructed_area = models.IntegerField(blank=True, null=True)
    school_fee = models.IntegerField(blank=True, null=True)
    school_name = models.CharField(max_length=30, null=True)
    bank_name = models.CharField(max_length=100, null=True)
    loan_amount = models.IntegerField(blank=True, null=True)
    college_fee = models.IntegerField(blank=True, null=True)
    college_name = models.CharField(max_length=30, null=True)
    income_certificate = models.FileField(null=False, blank=False, default='', upload_to='scholarships/mcm/income_certificate/')
    Marksheet = models.FileField(null=True, blank=True, default='', upload_to='scholarships/mcm/marksheet/')
    Bank_details = models.FileField(null=True, blank=True, default='', upload_to='scholarships/mcm/bank_details/')
    Affidavit = models.FileField(null=True, blank=True, default='', upload_to='scholarships/mcm/affidavit/')
    Aadhar_card = models.FileField(null=True, blank=True, default='', upload_to='scholarships/mcm/aadhar_card/')
    Fee_Receipt = models.FileField(null=True, blank=True, default='', upload_to='scholarships/mcm/fee_receipt/')
    
    parent_status = models.CharField(max_length=50, choices=Constants.PARENT_STATUS_CHOICES, default='Both Parents Alive', null=True, blank=True)
    single_parent = models.BooleanField(default=False)
    mother_income_certificate = models.FileField(null=True, blank=True, upload_to='scholarships/mcm/mother_income_certificate/')
    caste_certificate = models.FileField(null=True, blank=True, upload_to='scholarships/mcm/caste_certificate/')
    score_card = models.FileField(null=True, blank=True, upload_to='scholarships/mcm/score_card/')
    undertaking_form = models.FileField(null=True, blank=True, upload_to='scholarships/mcm/undertaking_form/')
    application_form = models.FileField(null=True, blank=True, upload_to='scholarships/mcm/application_form/')
    death_certificate = models.FileField(null=True, blank=True, upload_to='scholarships/mcm/death_certificate/')
    generated_pdf = models.FileField(null=True, blank=True, upload_to='scholarships/mcm/generated_pdf/')
    
    forms = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    remarks = models.TextField(null=True, blank=True)
    student = models.ForeignKey(Student,
                                on_delete=models.CASCADE, related_name='mcm_info')
    annual_income = models.IntegerField(default=0)
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(Award_and_scholarship, default=4, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Mcm'

    def __str__(self):
        return str(self.student)

class SingleParent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='single_parent_info')
    parent_type = models.CharField(max_length=10, choices=Constants.SINGLE_PARENT_CHOICES, default='FATHER')
    parent_name = models.CharField(max_length=50)
    parent_occupation = models.CharField(max_length=100)
    annual_income = models.IntegerField(default=0)
    income_certificate = models.FileField(null=False, blank=False, default='', upload_to='scholarships/single_parent/income_certificate/')
    death_certificate = models.FileField(null=False, blank=False, default='', upload_to='scholarships/single_parent/death_certificate/')
    cpi = models.FloatField(null=True, blank=True)
    mother_income_certificate = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/mother_income_certificate/')
    Marksheet = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/marksheet/')
    last_sem_result = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/last_sem_result/')
    Bank_details = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/bank_details/')
    Fee_Receipt = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/fee_receipt/')
    Affidavit = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/affidavit/')
    score_card = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/score_card/')
    undertaking_form = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/undertaking_form/')
    application_form = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/application_form/')
    caste_certificate = models.FileField(null=True, blank=True, upload_to='scholarships/single_parent/caste_certificate/')
    status = models.CharField(max_length=20, choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    remarks = models.TextField(null=True, blank=True)
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)

    class Meta:
        db_table = 'SingleParent'

    def __str__(self):
        return str(self.student)

class Notional_prize(models.Model):
    spi = models.FloatField()
    cpi = models.FloatField()
    year = models.CharField(max_length=10, choices=Constants.BATCH)
    award_id = models.ForeignKey(Award_and_scholarship, default=4, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Notional_prize'

#Addition: a column programme added
class Previous_winner(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    programme = models.CharField(max_length=10,default='B.Tech')
    year = models.IntegerField(default=datetime.datetime.now().year)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Previous_winner'

class Release(models.Model):
    date_time = models.DateTimeField(default=datetime.datetime.now, blank=True)
    programme = models.CharField(max_length=10,default='B.Tech')
    startdate = models.DateField(default=datetime.date.today)
    enddate = models.DateField()
    award = models.CharField(default='',max_length=50)
    remarks = models.TextField(max_length=500,default='')
    batch = models.TextField(default='all')
    notif_visible = models.IntegerField(default=1)

    class Meta:
        db_table = 'Release'

# new class added for keeping track of notifications and applied application by students
class Notification(models.Model):
    release_id = models.ForeignKey(Release,default=None, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete = models.CASCADE)
    notification_mcm_flag = models.BooleanField(default=False)
    notification_convocation_flag = models.BooleanField(default=False)
    invite_mcm_accept_flag = models.BooleanField(default=False)
    invite_convocation_accept_flag = models.BooleanField(default=False)
    def __str__(self):
        return str(self.student_id)

    class Meta:
        db_table = 'Notification'

class Application(models.Model):
    application_id = models.CharField(max_length = 100, primary_key=True)
    student_id = models.ForeignKey(ExtraInfo, on_delete = models.CASCADE)
    applied_flag = models.BooleanField(default=False)
    award = models.CharField(max_length = 30)

    def __str__(self):
        return str(self.application_id)

    class Meta:
        db_table = 'Application'

class Director_silver(models.Model):
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    correspondence_address = models.TextField(max_length=150, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE, default=3)
    award_type = models.CharField(max_length=50, null=True)
    status = models.CharField(max_length=20, choices=Constants.STATUS_CHOICES,default='INCOMPLETE')
    Marksheet = models.FileField(null=False, blank=False, default='', upload_to='scholarships/director_silver/marksheet/')
    date = models.DateField(default=datetime.date.today)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    inside_achievements = models.TextField(max_length=1000, null=True)
    justification = models.TextField(max_length=1000, null=True)
    outside_achievements = models.TextField(max_length=1000, null=True)

    class Meta:
        db_table = 'Director_silver'

class Proficiency_dm(models.Model):
    Marksheet = models.FileField(null=False, blank=False, default='', upload_to='scholarships/proficiency_dm/marksheet/')
    title_name = models.CharField(max_length=30, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE, default=4)
    award_type = models.CharField(max_length=50, null=True)
    status = models.CharField(max_length=20, choices=Constants.STATUS_CHOICES,default='INCOMPLETE')
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    correspondence_address = models.TextField(max_length=150, null=True)
    no_of_students = models.IntegerField(default=1)
    date = models.DateField(default=datetime.date.today)
    roll_no1 = models.CharField(max_length=30, null=True)
    roll_no2 = models.CharField(max_length=30, null=True)
    roll_no3 = models.CharField(max_length=30, null=True)
    roll_no4 = models.CharField(max_length=30, null=True)
    roll_no5 = models.CharField(max_length=30, null=True)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    brief_description = models.TextField(max_length=1000 ,null=True)
    justification = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    ece_topic = models.CharField(max_length=25,null=True)
    cse_topic = models.CharField(max_length=25,null=True)
    mech_topic = models.CharField(max_length=25,null=True)
    design_topic = models.CharField(max_length=25,null=True)
    ece_percentage = models.FloatField(null=True)
    cse_percentage = models.FloatField(null=True)
    mech_percentage = models.FloatField(null=True)
    design_percentage = models.FloatField(null=True)
    correspondence_address = models.CharField(max_length=100, null=True)
    financial_assistance = models.TextField(max_length=1000, null=True)
    grand_total = models.IntegerField(null=True)
    nearest_policestation = models.CharField(max_length=25, null=True)
    nearest_railwaystation = models.CharField(max_length=25, null=True)


    class Meta:
        db_table = 'Proficiency_dm'

class Director_gold(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=20,choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    correspondence_address = models.TextField(max_length=40, default='address')
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    Marksheet = models.FileField(null=False, blank=False, default='', upload_to='scholarships/director_gold/marksheet/')
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(Award_and_scholarship, default=4, on_delete=models.CASCADE)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    academic_achievements = models.TextField(max_length=1000 ,null=True)
    science_inside = models.TextField(max_length=1000 ,null=True)
    science_outside = models.TextField(max_length=1000 ,null=True)
    games_inside = models.TextField(max_length=1000 ,null=True)
    games_outside = models.TextField(max_length=1000 ,null=True)
    cultural_inside = models.TextField(max_length=1000 ,null=True)
    cultural_outside = models.TextField(max_length=1000 ,null=True)
    social = models.TextField(max_length=1000 ,null=True)
    corporate = models.TextField(max_length=1000 ,null=True)
    hall_activities = models.TextField(max_length=1000 ,null=True)
    gymkhana_activities = models.TextField(max_length=1000 ,null=True)
    institute_activities = models.TextField(max_length=1000 ,null=True)
    counselling_activities = models.TextField(max_length=1000 ,null=True)
    other_activities = models.TextField(max_length=1000 ,null=True)
    justification = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    correspondence_address = models.CharField(max_length=100, null=True)
    financial_assistance = models.TextField(max_length=1000, null=True)
    grand_total = models.IntegerField(null=True)
    nearest_policestation = models.CharField(max_length=25, null=True)
    nearest_railwaystation = models.CharField(max_length=25, null=True)

    class Meta:
        db_table = 'Director_gold'
