# Create your views here.

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context,RequestContext

from events.forms import EventMeetingForm
from events.models import Event

from meetings.forms import MeetingAdditionForm as MAF
from meetings.models import Meeting

from meetings.forms import AnnounceSendForm as ASF
from meetings.forms import AnnounceCCSendForm as ACCSF
from meetings.models import AnnounceSend

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required, user_passes_test
from helpers.challenges import is_officer

import datetime

from emails.generators import generate_notice_email as generate_email
from emails.generators import generate_notice_cc_email
from emails.generators import DEFAULT_FROM_ADDR

@login_required
@user_passes_test(is_officer, login_url='/NOTOUCHING/')
def viewattendance(request,id):
    context = RequestContext(request)
    m = get_object_or_404(Meeting,pk=id)
    context['m'] = m
    
    now = datetime.datetime.now()
    now = m.datetime
    yest = now + datetime.timedelta(days=-1)
    morethanaweek = now + datetime.timedelta(days=7,hours=12)
    
    upcoming = Event.objects.filter(datetime_start__gte=yest,datetime_start__lte=morethanaweek)
    context['events'] = upcoming
    
    
    future = Event.objects.filter(datetime_start__gte=morethanaweek)
    context['future'] = future
    return render_to_response('meeting_view.html', context)

@login_required
@user_passes_test(is_officer, login_url='/NOTOUCHING/')
def updateevent(request,meetingid,eventid):
    context = RequestContext(request)
    context['msg'] = "Update Event"
    event = get_object_or_404(Event,pk=eventid)
    if request.method == 'POST':
        formset = EventMeetingForm(request.POST,instance=event)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse('meetings.views.viewattendance',args=(meetingid,)))
        else:
            context['formset'] = formset
    else:
        formset = EventMeetingForm(instance=event)
        context['formset'] = formset
    return render_to_response('form_crispy.html', context)

@login_required
@user_passes_test(is_officer, login_url='/NOTOUCHING/')
def editattendance(request,id):
    context = RequestContext(request)
    context['msg'] = "Edit Meeting"
    m = get_object_or_404(Meeting,pk=id)
    if request.method == 'POST':
        formset = MAF(request.POST,instance=m)
        if formset.is_valid():
            m = formset.save()
            return HttpResponseRedirect(reverse('meetings.views.viewattendance',args=(m.id,)))
        else:
            context['formset'] = formset
    else:
        formset = MAF(instance=m)
        context['formset'] = formset
    return render_to_response('form_crispy.html', context)
        
@login_required
@user_passes_test(is_officer, login_url='/NOTOUCHING/')
def listattendance(request,page=1):
    context = RequestContext(request)
    attend = Meeting.objects.all()
    paginated = Paginator(attend,10)

    try:
        attend = paginated.page(page)
    except:
        attend = paginated.page(1)
        
    context['attend'] = attend
    return render_to_response('meeting_list.html', context)
        
@login_required
@user_passes_test(is_officer, login_url='/NOTOUCHING/')
def newattendance(request):
    context = RequestContext(request)
    if request.method == 'POST':
        formset = MAF(request.POST)
        if formset.is_valid():
            m = formset.save()
            return HttpResponseRedirect(reverse('meetings.views.viewattendance',args=(m.id,)))
        else:
            context['formset'] = formset
            context['msg'] = "New Meeting (Errors In Form)"
    else:
        formset = MAF()
        context['formset'] = formset
        context['msg'] = "New Meeting"
    return render_to_response('form_crispy.html', context)


@login_required
@user_passes_test(is_officer, login_url='/NOTOUCHING/')
def mknotice(request,id):
    context = RequestContext(request)
    
    meeting = get_object_or_404(Meeting,pk=id)
    
    if request.method == 'POST':
        formset = ASF(meeting,request.POST)
        if formset.is_valid():
            notice = formset.save()
            email = generate_email(notice)
            res = email.send()
            if res == 1:
                success = True
            else:
                success = False
            AnnounceSend.objects.create(announce=notice,sent_success=success)
            
            return HttpResponseRedirect(reverse('meetings.views.viewattendance',args=(meeting.id,)))
        else:
            context['formset'] = formset
    
    else:
        formset = ASF(meeting)
        context['formset'] = formset
        context['msg'] = "New Meeting Notice"
    return render_to_response('form_crispy.html',context)


def mkccnotice(request,id):
    context = RequestContext(request)
    
    meeting = get_object_or_404(Meeting,pk=id)
    
    if request.method == 'POST':
        formset = ACCSF(meeting,request.POST)
        if formset.is_valid():
            notice = formset.save()
            email = generate_notice_cc_email(notice)
            res = email.send()
            if res == 1:
                notice.sent_success = True
            else:
                notice.sent_success = False
                
            notice.save()
            
            return HttpResponseRedirect(reverse('meetings.views.viewattendance',args=(meeting.id,)))
        else:
            context['formset'] = formset
    
    else:
        formset = ACCSF(meeting)
        context['formset'] = formset
        context['msg'] = "New Meeting Notice"
    return render_to_response('form_crispy.html',context)