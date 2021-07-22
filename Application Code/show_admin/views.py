from common.decorator import result_declared
from candi_register.models import Candidate
import os
from user_auth.models import Profile
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http.response import HttpResponse
from voter.models import ElectionStatus
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
import pandas as pd
import random
import numpy as np
import string
from django.core.mail import send_mail

# Create your views here.
# registration time
@login_required
def admin(request):
    try:
        if ElectionStatus.objects.all()[0].is_active:
            if ElectionStatus.objects.all()[0].poll_started==False:
                if ElectionStatus.objects.all()[0].result_declared==False:
                    # registration time
                    # as election=true, poll=false, result = false
                    # button - start poll
                    status = 'registration-time'
                else:
                    # as election=true, poll=false, result = true
                    # button - stop election
                    status = 'stop-election'
            else:
                # as election=true, poll=true, result = false
                # button - stop polling
                status='polling'
        else:
            # as election=false, poll=false, result = false
            # button - start election
            status='no-active-election'
    except:
        # This will be executed only once
        status='no-active-election'
    return render(request, 'show_admin/admin.html', {'status':status})

@login_required
def operation(request):
    failed_email = []
    data = request.POST
    np.random.seed = 347
    create_password = lambda:''.join([random.choice(string.ascii_letters) for i in range(5)]+[random.choice(string.digits) for i in range(5)]+[random.choice(string.punctuation) for i in range(5)])
    stud_path = os.path.join(os.path.dirname('__file__'), 'show_admin', 'user_list', 'students.csv')
    if data['next']=='Create User':
        students = pd.read_csv(stud_path)
        for studemail in students:
            user = User.objects.create_user(username=studemail, password=create_password())
            user.save()
            profile = Profile()
            profile.user = request.user
            profile.is_voter = True
            profile.save()            
    try:
        election = ElectionStatus.objects.all()[0]
    except:
        election = ElectionStatus()
    if data['next']=='Start Election':
        students = pd.read_csv(stud_path)
        for studemail in students:
            user = User.objects.get(username=studemail)
            pasw = create_password()
            user.set_password(pasw)
            user.save()
            try:
                send_mail(
                    'Credentials For Upcoming Election',
                    f'Username: {studemail}\nPassword:{pasw}\nDo not share this credentials with anyone in any case.',
                    'from@example.com',
                    ['to@example.com'],
                    fail_silently=False,
                )
            except:
                failed_email.append(studemail)
            failed = np.array(failed_email)
            np.savetxt("failed.csv", failed, delimiter = ",")   
        if (len(failed_email)/len(students))==0.0:
            election.is_active = True
            election.save()
        else: 
            return HttpResponse("<h4>Election is not started as all the students have not recieved the email</h4>")
    if data['next']=='Start Polling':
        election.poll_started = True
        election.save()
    if data['next']=='Stop Polling':
        election.poll_started = False
        election.result_declared = True
        return HttpResponseRedirect(reverse('show_admin:result'))
    if data['next']=='Stop Election':
        election.is_active = False
    return HttpResponseRedirect(reverse('show_admin:admin'))

@result_declared
def result(request):
    candi = Candidate.objects.all()
    result = {}
    POSITION = {
            'Vice President',
            'General Secretary',
            'Literary Secretary',
            'Cultural Secretary',
            'Sports Secretary',
            'Girls Mess Secretary',
            'Boys Mess Secretary'
        }
    
    for position in POSITION:
        try:
            result[position] = candi.filter(position=position).order_by('-result')[0]
        except:
            pass
    return render(request, 'show_admin/result.html', {'result':result})
        
        