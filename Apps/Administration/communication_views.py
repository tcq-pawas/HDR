from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from Apps.Agent.models import Communication
from .forms import AdminCommunicationForm
from django.core.mail import send_mail
from django.conf import settings
import urllib.parse
from django.core.paginator import Paginator
from Apps.Administration.smart_dashboard_views import AdminDashboardMixin

class AdminCommunicationListView(AdminDashboardMixin, ListView):
    model = Communication
    template_name = 'administration/communication_list.html'
    context_object_name = 'communications'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Communication.objects.filter(agent=self.request.user).order_by('-sent_at')
        type_filter = self.request.GET.get('type')
        if type_filter:
            queryset = queryset.filter(communication_type=type_filter)
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_filter'] = self.request.GET.get('type', '')
        return context

class AdminCommunicationSendView(AdminDashboardMixin, View):
    def get(self, request):
        form = AdminCommunicationForm()
        return render(request, 'administration/communication_form.html', {'form': form})
        
    def post(self, request):
        form = AdminCommunicationForm(request.POST)
        if form.is_valid():
            communication = form.save(commit=False)
            communication.agent = request.user
            
            if communication.communication_type == 'email':
                try:
                    send_mail(
                        subject=communication.subject,
                        message=communication.message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[communication.recipient],
                        fail_silently=False,
                    )
                    communication.status = 'sent'
                    messages.success(request, "Email sent successfully!")
                except Exception as e:
                    communication.status = 'failed'
                    communication.notes = f"Failed to send email: {str(e)}"
                    messages.error(request, f"Failed to send email: {str(e)}")
                communication.save()
                return redirect('admin_dash:communication-list')
                
            elif communication.communication_type == 'whatsapp':
                phone = communication.recipient.strip()
                clean_phone = ''.join(c for c in phone if c.isdigit())
                if len(clean_phone) == 10:
                    clean_phone = '91' + clean_phone
                
                whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={urllib.parse.quote(communication.message)}"
                
                communication.status = 'sent'
                communication.save()
                messages.success(request, "Message saved! WhatsApp opened in a new tab.")
                return redirect(whatsapp_url)
        
        return render(request, 'administration/communication_form.html', {'form': form})
