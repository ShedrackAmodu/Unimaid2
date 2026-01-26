"""
Comprehensive bulk actions for Django admin panel.
This module provides reusable bulk action functions for all admin models.
"""

from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models import Q

# Import all models
from apps.accounts.models import LibraryUser, StudyRoom, StudyRoomBooking
from apps.catalog.models import Author, Publisher, Faculty, Department, Topic, Genre, Book, BookCopy
from apps.circulation.models import Loan, Reservation, Fine, LoanRequest, Attendance
from apps.events.models import Event, EventRegistration
from apps.repository.models import Collection, EBook, EBookPermission
from apps.blog.models import BlogPost, StaticPage, FeaturedContent, News


class BulkActionMixin:
    """Mixin providing common bulk action functionality."""
    
    def get_bulk_action_message(self, action_name, count, errors=None):
        """Generate a user-friendly message for bulk actions."""
        if errors:
            return f"{action_name} completed: {count} successful, {len(errors)} failed."
        return f"Successfully {action_name} {count} items."


def bulk_activate_users(modeladmin, request, queryset):
    """Activate selected users."""
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request, 
        f"Successfully activated {updated} users.",
        messages.SUCCESS
    )
bulk_activate_users.short_description = "Activate selected users"


def bulk_deactivate_users(modeladmin, request, queryset):
    """Deactivate selected users."""
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request, 
        f"Successfully deactivated {updated} users.",
        messages.SUCCESS
    )
bulk_deactivate_users.short_description = "Deactivate selected users"


def bulk_update_membership_type(modeladmin, request, queryset):
    """Update membership type for selected users."""
    from django import forms
    from django.shortcuts import render, redirect
    from django.urls import reverse
    
    if 'apply' in request.POST:
        membership_type = request.POST.get('membership_type')
        if membership_type:
            updated = queryset.update(membership_type=membership_type)
            modeladmin.message_user(
                request, 
                f"Successfully updated membership type for {updated} users.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'users': queryset,
        'title': 'Update Membership Type',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_update_membership.html', context)
bulk_update_membership_type.short_description = "Update membership type"


def bulk_assign_department(modeladmin, request, queryset):
    """Assign department to selected users."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        department_id = request.POST.get('department')
        if department_id:
            try:
                from apps.catalog.models import Department
                department = Department.objects.get(id=department_id)
                updated = queryset.update(department=department)
                modeladmin.message_user(
                    request, 
                    f"Successfully assigned department to {updated} users.",
                    messages.SUCCESS
                )
                return redirect(request.get_full_path())
            except Department.DoesNotExist:
                modeladmin.message_user(
                    request, 
                    "Selected department does not exist.",
                    messages.ERROR
                )
    
    departments = Department.objects.all()
    context = {
        'users': queryset,
        'departments': departments,
        'title': 'Assign Department',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_assign_department.html', context)
bulk_assign_department.short_description = "Assign department"


def bulk_update_study_room_status(modeladmin, request, queryset):
    """Update status for selected study rooms."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        is_active = request.POST.get('is_active') == 'true'
        updated = queryset.update(is_active=is_active)
        status_text = "activated" if is_active else "deactivated"
        modeladmin.message_user(
            request, 
            f"Successfully {status_text} {updated} study rooms.",
            messages.SUCCESS
        )
        return redirect(request.get_full_path())
    
    context = {
        'rooms': queryset,
        'title': 'Update Study Room Status',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_update_room_status.html', context)
bulk_update_study_room_status.short_description = "Update study room status"


def bulk_update_booking_status(modeladmin, request, queryset):
    """Update status for selected study room bookings."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        status = request.POST.get('status')
        if status:
            updated = queryset.update(status=status)
            modeladmin.message_user(
                request, 
                f"Successfully updated status for {updated} bookings.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'bookings': queryset,
        'title': 'Update Booking Status',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'status_choices': StudyRoomBooking.STATUS_CHOICES,
    }
    return render(request, 'admin/bulk_update_booking_status.html', context)
bulk_update_booking_status.short_description = "Update booking status"


def bulk_update_book_status(modeladmin, request, queryset):
    """Update status for selected books."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        status = request.POST.get('status')
        if status:
            updated = queryset.update(status=status)
            modeladmin.message_user(
                request, 
                f"Successfully updated status for {updated} books.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'books': queryset,
        'title': 'Update Book Status',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'status_choices': BookCopy.STATUS_CHOICES,
    }
    return render(request, 'admin/bulk_update_book_status.html', context)
bulk_update_book_status.short_description = "Update book status"


def bulk_update_book_condition(modeladmin, request, queryset):
    """Update condition for selected books."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        condition = request.POST.get('condition')
        if condition:
            updated = queryset.update(condition=condition)
            modeladmin.message_user(
                request, 
                f"Successfully updated condition for {updated} books.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'books': queryset,
        'title': 'Update Book Condition',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'condition_choices': BookCopy.CONDITION_CHOICES,
    }
    return render(request, 'admin/bulk_update_book_condition.html', context)
bulk_update_book_condition.short_description = "Update book condition"


def bulk_update_book_location(modeladmin, request, queryset):
    """Update location for selected books."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        location = request.POST.get('location')
        if location:
            updated = queryset.update(location=location)
            modeladmin.message_user(
                request, 
                f"Successfully updated location for {updated} books.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'books': queryset,
        'title': 'Update Book Location',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_update_book_location.html', context)
bulk_update_book_location.short_description = "Update book location"


def bulk_assign_authors(modeladmin, request, queryset):
    """Assign authors to selected books."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        author_ids = request.POST.getlist('authors')
        if author_ids:
            try:
                authors = Author.objects.filter(id__in=author_ids)
                for book in queryset:
                    book.authors.add(*authors)
                modeladmin.message_user(
                    request, 
                    f"Successfully assigned authors to {queryset.count()} books.",
                    messages.SUCCESS
                )
                return redirect(request.get_full_path())
            except Author.DoesNotExist:
                modeladmin.message_user(
                    request, 
                    "One or more selected authors do not exist.",
                    messages.ERROR
                )
    
    authors = Author.objects.all()
    context = {
        'books': queryset,
        'authors': authors,
        'title': 'Assign Authors',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_assign_authors.html', context)
bulk_assign_authors.short_description = "Assign authors"


def bulk_assign_topics(modeladmin, request, queryset):
    """Assign topics to selected books."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        topic_id = request.POST.get('topic')
        if topic_id:
            try:
                topic = Topic.objects.get(id=topic_id)
                updated = queryset.update(topic=topic)
                modeladmin.message_user(
                    request, 
                    f"Successfully assigned topic to {updated} books.",
                    messages.SUCCESS
                )
                return redirect(request.get_full_path())
            except Topic.DoesNotExist:
                modeladmin.message_user(
                    request, 
                    "Selected topic does not exist.",
                    messages.ERROR
                )
    
    topics = Topic.objects.all()
    context = {
        'books': queryset,
        'topics': topics,
        'title': 'Assign Topic',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_assign_topic.html', context)
bulk_assign_topics.short_description = "Assign topic"


def bulk_update_loan_status(modeladmin, request, queryset):
    """Update status for selected loans."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        status = request.POST.get('status')
        if status:
            updated = queryset.update(status=status)
            modeladmin.message_user(
                request, 
                f"Successfully updated status for {updated} loans.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'loans': queryset,
        'title': 'Update Loan Status',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'status_choices': Loan.STATUS_CHOICES,
    }
    return render(request, 'admin/bulk_update_loan_status.html', context)
bulk_update_loan_status.short_description = "Update loan status"


def bulk_extend_loans(modeladmin, request, queryset):
    """Extend due date for selected loans."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        days = request.POST.get('days', 7)
        try:
            days = int(days)
            if days > 0:
                updated = 0
                for loan in queryset.filter(status='active'):
                    loan.due_date = loan.due_date + timezone.timedelta(days=days)
                    loan.save()
                    updated += 1
                
                modeladmin.message_user(
                    request, 
                    f"Successfully extended {updated} loans by {days} days.",
                    messages.SUCCESS
                )
                return redirect(request.get_full_path())
        except ValueError:
            modeladmin.message_user(
                request, 
                "Please enter a valid number of days.",
                messages.ERROR
            )
    
    context = {
        'loans': queryset,
        'title': 'Extend Loans',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_extend_loans.html', context)
bulk_extend_loans.short_description = "Extend selected loans"


def bulk_calculate_fines(modeladmin, request, queryset):
    """Calculate fines for selected loans."""
    updated = 0
    errors = []
    
    for loan in queryset.filter(status='overdue'):
        try:
            # Calculate fine based on overdue days
            overdue_days = (timezone.now().date() - loan.due_date).days
            fine_amount = overdue_days * 100  # 100 naira per day
            
            fine, created = Fine.objects.get_or_create(
                loan=loan,
                defaults={
                    'amount': fine_amount,
                    'reason': f'Overdue by {overdue_days} days',
                    'status': 'pending'
                }
            )
            
            if not created:
                fine.amount = fine_amount
                fine.save()
            
            updated += 1
        except Exception as e:
            errors.append(f"Error processing loan {loan.id}: {str(e)}")
    
    if updated > 0:
        modeladmin.message_user(
            request, 
            f"Successfully calculated fines for {updated} loans.",
            messages.SUCCESS
        )
    
    if errors:
        for error in errors:
            modeladmin.message_user(request, error, messages.ERROR)
bulk_calculate_fines.short_description = "Calculate fines for selected loans"


def bulk_process_reservations(modeladmin, request, queryset):
    """Process selected reservations."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        status = request.POST.get('status')
        if status:
            updated = queryset.update(status=status)
            modeladmin.message_user(
                request, 
                f"Successfully updated status for {updated} reservations.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'reservations': queryset,
        'title': 'Process Reservations',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'status_choices': Reservation.STATUS_CHOICES,
    }
    return render(request, 'admin/bulk_process_reservations.html', context)
bulk_process_reservations.short_description = "Process selected reservations"


def bulk_checkout_visitors(modeladmin, request, queryset):
    """Check out selected visitors."""
    updated = 0
    for attendance in queryset.filter(status='active'):
        attendance.check_out_visitor()
        updated += 1
    
    modeladmin.message_user(
        request, 
        f"Successfully checked out {updated} visitors.",
        messages.SUCCESS
    )
bulk_checkout_visitors.short_description = "Check out selected visitors"


def bulk_update_event_status(modeladmin, request, queryset):
    """Update status for selected events."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        status = request.POST.get('status')
        if status:
            updated = queryset.update(status=status)
            modeladmin.message_user(
                request, 
                f"Successfully updated status for {updated} events.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'events': queryset,
        'title': 'Update Event Status',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'status_choices': Event.STATUS_CHOICES,
    }
    return render(request, 'admin/bulk_update_event_status.html', context)
bulk_update_event_status.short_description = "Update event status"


def bulk_update_ebook_access_level(modeladmin, request, queryset):
    """Update access level for selected eBooks."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        access_level = request.POST.get('access_level')
        if access_level:
            updated = queryset.update(access_level=access_level)
            modeladmin.message_user(
                request, 
                f"Successfully updated access level for {updated} eBooks.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'ebooks': queryset,
        'title': 'Update eBook Access Level',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'access_level_choices': EBook.ACCESS_LEVEL_CHOICES,
    }
    return render(request, 'admin/bulk_update_ebook_access.html', context)
bulk_update_ebook_access_level.short_description = "Update eBook access level"


def bulk_update_blog_status(modeladmin, request, queryset):
    """Update status for selected blog posts."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        status = request.POST.get('status')
        if status:
            updated = queryset.update(status=status)
            modeladmin.message_user(
                request, 
                f"Successfully updated status for {updated} blog posts.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'posts': queryset,
        'title': 'Update Blog Post Status',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'status_choices': BlogPost.STATUS_CHOICES,
    }
    return render(request, 'admin/bulk_update_blog_status.html', context)
bulk_update_blog_status.short_description = "Update blog post status"


def bulk_update_news_status(modeladmin, request, queryset):
    """Update status for selected news items."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        status = request.POST.get('status')
        if status:
            updated = queryset.update(status=status)
            modeladmin.message_user(
                request, 
                f"Successfully updated status for {updated} news items.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
    
    context = {
        'news_items': queryset,
        'title': 'Update News Status',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'status_choices': News.STATUS_CHOICES,
    }
    return render(request, 'admin/bulk_update_news_status.html', context)
bulk_update_news_status.short_description = "Update news status"


def bulk_update_static_page_status(modeladmin, request, queryset):
    """Update status for selected static pages."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        is_active = request.POST.get('is_active') == 'true'
        updated = queryset.update(is_active=is_active)
        status_text = "activated" if is_active else "deactivated"
        modeladmin.message_user(
            request, 
            f"Successfully {status_text} {updated} static pages.",
            messages.SUCCESS
        )
        return redirect(request.get_full_path())
    
    context = {
        'pages': queryset,
        'title': 'Update Static Page Status',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_update_page_status.html', context)
bulk_update_static_page_status.short_description = "Update static page status"


def bulk_update_featured_content_order(modeladmin, request, queryset):
    """Update order for selected featured content."""
    from django import forms
    from django.shortcuts import render, redirect
    
    if 'apply' in request.POST:
        order = request.POST.get('order', 0)
        try:
            order = int(order)
            updated = queryset.update(order=order)
            modeladmin.message_user(
                request, 
                f"Successfully updated order for {updated} featured content items.",
                messages.SUCCESS
            )
            return redirect(request.get_full_path())
        except ValueError:
            modeladmin.message_user(
                request, 
                "Please enter a valid order number.",
                messages.ERROR
            )
    
    context = {
        'featured_items': queryset,
        'title': 'Update Featured Content Order',
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return render(request, 'admin/bulk_update_featured_order.html', context)
bulk_update_featured_content_order.short_description = "Update featured content order"


# List of all bulk actions for easy import
ALL_BULK_ACTIONS = [
    bulk_activate_users,
    bulk_deactivate_users,
    bulk_update_membership_type,
    bulk_assign_department,
    bulk_update_study_room_status,
    bulk_update_booking_status,
    bulk_update_book_status,
    bulk_update_book_condition,
    bulk_update_book_location,
    bulk_assign_authors,
    bulk_assign_topics,
    bulk_update_loan_status,
    bulk_extend_loans,
    bulk_calculate_fines,
    bulk_process_reservations,
    bulk_checkout_visitors,
    bulk_update_event_status,
    bulk_update_ebook_access_level,
    bulk_update_blog_status,
    bulk_update_news_status,
    bulk_update_static_page_status,
    bulk_update_featured_content_order,
]