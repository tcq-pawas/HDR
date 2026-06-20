import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView, DeleteView
from django.contrib.auth.models import User, Group
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.forms import PasswordResetForm
from django.utils.decorators import method_decorator
from Apps.Administration.smart_dashboard_views import AdminDashboardMixin
from Apps.Investor.models import InvestorProfile, Investment

class InvestorListView(AdminDashboardMixin, ListView):
    model = InvestorProfile
    template_name = 'administration/investors/investor_list.html'
    context_object_name = 'investors'
    
    def get_queryset(self):
        return InvestorProfile.objects.select_related('user').all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['total_investors'] = qs.count()
        context['active_investors'] = sum(1 for p in qs if p.user.is_active)
        context['suspended_investors'] = context['total_investors'] - context['active_investors']
        return context

class InvestorCreateView(AdminDashboardMixin, TemplateView):
    template_name = 'administration/investors/investor_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        status = request.POST.get('status', 'active')

        if not email:
            messages.error(request, "Email is required.")
            return self.get(request, *args, **kwargs)

        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return self.get(request, *args, **kwargs)

        username = email.split('@')[0]
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user with random unusable password initially
        random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        user = User.objects.create_user(
            username=username,
            email=email,
            password=random_password,
            first_name=first_name,
            last_name=last_name,
            is_active=(status == 'active')
        )

        # Assign to investor group
        investor_group, _ = Group.objects.get_or_create(name='investor')
        user.groups.add(investor_group)

        # Create Investor Profile
        InvestorProfile.objects.create(
            user=user,
            phone=phone,
            verified=(status == 'active')
        )

        # Send password reset email for invitation
        form = PasswordResetForm({'email': user.email})
        if form.is_valid():
            request_origin = request.scheme + '://' + request.get_host()
            form.save(
                request=request,
                use_https=request.is_secure(),
                subject_template_name='administration/emails/investor_invitation_subject.txt',
                email_template_name='administration/emails/investor_invitation.html',
                html_email_template_name='administration/emails/investor_invitation.html',
            )

        messages.success(request, f"Investor {first_name} {last_name} created successfully. An invitation email has been sent.")
        return redirect('admin_dash:investor-list')

class InvestorDetailView(AdminDashboardMixin, DetailView):
    model = InvestorProfile
    template_name = 'administration/investors/investor_detail.html'
    context_object_name = 'profile'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        user = profile.user
        
        context['investments'] = Investment.objects.filter(investor=user).select_related('listing', 'listing__property_obj')
        return context

class InvestorUpdateView(AdminDashboardMixin, TemplateView):
    template_name = 'administration/investors/investor_update.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(InvestorProfile, id=self.kwargs['pk'])
        context['profile'] = profile
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(InvestorProfile, id=self.kwargs['pk'])
        user = profile.user
        
        new_email = request.POST.get('email')
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                messages.error(request, f"The email {new_email} is already in use.")
                return redirect('admin_dash:investor-update', pk=profile.pk)
            user.email = new_email
            
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.is_active = (request.POST.get('status') == 'active')
        user.save()
        
        profile.phone = request.POST.get('phone', profile.phone)
        profile.company_name = request.POST.get('company_name', profile.company_name)
        profile.save()
        
        messages.success(request, "Investor profile updated successfully.")
        return redirect('admin_dash:investor-detail', pk=profile.pk)

class InvestorDeleteView(AdminDashboardMixin, DeleteView):
    model = InvestorProfile
    success_url = reverse_lazy('admin_dash:investor-list')
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        profile = self.get_object()
        user = profile.user
        
        # Delete profile and user
        profile.delete()
        user.delete()
        
class InvestorToggleStatusView(AdminDashboardMixin, DetailView):
    model = InvestorProfile
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        profile = self.get_object()
        user = profile.user
        
        if user.is_active:
            user.is_active = False
            action = "suspended"
        else:
            user.is_active = True
            action = "activated"
            
        user.save()
        messages.success(request, f"Investor account for {user.username} has been {action} successfully.")
        
        return redirect('admin_dash:investor-list')
