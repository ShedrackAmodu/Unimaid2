from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import Event
from .forms import EventForm, EventRegistrationForm


def is_staff_user(user):
    return user.groups.filter(name='Staff').exists() or user.is_staff


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 10

    def get_queryset(self):
        return Event.objects.filter(date__gte=timezone.now().date()).order_by('date', 'time')


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        context['can_register'] = (
            self.request.user.is_authenticated and
            event.registration_deadline and
            timezone.now() < event.registration_deadline and
            (not event.max_attendees or event.registrations.count() < event.max_attendees)
        )
        context['is_registered'] = (
            self.request.user.is_authenticated and
            event.registrations.filter(user=self.request.user).exists()
        )
        return context


@login_required
def register_for_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    # Check if registration is allowed
    if not event.registration_deadline or timezone.now() > event.registration_deadline:
        messages.error(request, 'Registration deadline has passed.')
        return redirect('events:event_detail', pk=event_id)

    if event.max_attendees and event.registrations.count() >= event.max_attendees:
        messages.error(request, 'Event is fully booked.')
        return redirect('events:event_detail', pk=event_id)

    # Check if user is already registered
    if event.registrations.filter(user=request.user).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('events:event_detail', pk=event_id)

    # Create registration
    event.registrations.create(user=request.user)
    messages.success(request, f'Successfully registered for "{event.title}".')
    return redirect('events:event_detail', pk=event_id)


@login_required
def unregister_from_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    registration = event.registrations.filter(user=request.user).first()

    if registration:
        registration.delete()
        messages.success(request, f'Unregistered from "{event.title}".')
    else:
        messages.warning(request, 'You are not registered for this event.')

    return redirect('events:event_detail', pk=event_id)


@login_required
@user_passes_test(is_staff_user)
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form, 'action': 'Create'})


@login_required
@user_passes_test(is_staff_user)
def edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    return render(request, 'events/event_form.html', {'form': form, 'action': 'Edit', 'event': event})


@login_required
@user_passes_test(is_staff_user)
def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('events:event_list')
    return render(request, 'events/event_confirm_delete.html', {'event': event})
