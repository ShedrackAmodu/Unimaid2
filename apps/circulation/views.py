from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from .models import Loan, Reservation, Fine, LoanRequest
from apps.catalog.models import Book, BookCopy
from apps.accounts.models import LibraryUser


def is_staff_user(user):
    return user.groups.filter(name='Staff').exists() or user.is_staff


@login_required
@user_passes_test(is_staff_user)
def staff_dashboard(request):
    pending_loans = Loan.objects.filter(status='active').select_related('user', 'book_copy__book')
    pending_reservations = Reservation.objects.filter(status='active').select_related('user', 'book')
    pending_borrow_requests = LoanRequest.objects.filter(status='pending').select_related('user', 'book_copy__book')
    overdue_loans = Loan.objects.filter(status='active', due_date__lt=timezone.now()).select_related('user', 'book_copy__book')
    recent_returns = Loan.objects.filter(status='returned').order_by('-return_date')[:10]

    context = {
        'pending_loans': pending_loans,
        'pending_reservations': pending_reservations,
        'pending_borrow_requests': pending_borrow_requests,
        'overdue_loans': overdue_loans,
        'recent_returns': recent_returns,
    }
    return render(request, 'circulation/staff_dashboard.html', context)


@login_required
def patron_dashboard(request):
    user = request.user
    current_loans = Loan.objects.filter(user=user, status='active').select_related('book_copy__book')
    active_reservations = Reservation.objects.filter(user=user, status='active').select_related('book')
    pending_borrow_requests = LoanRequest.objects.filter(user=user, status='pending').select_related('book_copy__book')
    loan_history = Loan.objects.filter(user=user).exclude(status='active').order_by('-return_date')[:10]
    unpaid_fines = Fine.objects.filter(loan__user=user, status='unpaid')

    context = {
        'current_loans': current_loans,
        'active_reservations': active_reservations,
        'pending_borrow_requests': pending_borrow_requests,
        'loan_history': loan_history,
        'unpaid_fines': unpaid_fines,
        'total_fines': sum(fine.amount for fine in unpaid_fines),
    }
    return render(request, 'circulation/patron_dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def checkout_book(request):
    if request.method == 'POST':
        book_copy_id = request.POST.get('book_copy_id')
        user_id = request.POST.get('user_id')

        try:
            book_copy = BookCopy.objects.get(id=book_copy_id, status='available')
            user = get_object_or_404(LibraryUser, id=user_id)

            # Check if user has unpaid fines
            if Fine.objects.filter(loan__user=user, status='unpaid').exists():
                messages.error(request, 'User has unpaid fines. Cannot checkout book.')
                return redirect('circulation:checkout')

            # Create loan
            loan = Loan.objects.create(
                user=user,
                book_copy=book_copy,
                due_date=timezone.now() + timedelta(days=14)  # Default 14 days, will be recalculated
            )
            loan.due_date = loan.calculate_due_date()
            loan.save()

            # Update book copy status
            book_copy.status = 'checked_out'
            book_copy.save()

            messages.success(request, f'Book "{book_copy.book.title}" checked out to {user.get_full_name()}.')
            return redirect('circulation:staff_dashboard')

        except BookCopy.DoesNotExist:
            messages.error(request, 'Book copy not available.')
        except Exception as e:
            messages.error(request, f'Error during checkout: {str(e)}')

    available_copies = BookCopy.objects.filter(status='available').select_related('book')[:50]
    context = {
        'available_copies': available_copies,
    }
    return render(request, 'circulation/checkout.html', context)


@login_required
@user_passes_test(is_staff_user)
def return_book(request):
    if request.method == 'POST':
        loan_id = request.POST.get('loan_id')

        try:
            loan = Loan.objects.get(id=loan_id, status='active')
            loan.return_date = timezone.now()
            loan.status = 'returned'
            loan.save()

            # Update book copy status
            loan.book_copy.status = 'available'
            loan.book_copy.save()

            # Check for overdue and create fine if needed
            if loan.due_date < timezone.now():
                days_overdue = (timezone.now().date() - loan.due_date.date()).days
                fine_amount = days_overdue * 1.00  # $1 per day
                Fine.objects.create(
                    loan=loan,
                    amount=fine_amount,
                    reason=f'Overdue return: {days_overdue} days'
                )

            messages.success(request, f'Book "{loan.book_copy.book.title}" returned successfully.')
            return redirect('circulation:staff_dashboard')

        except Loan.DoesNotExist:
            messages.error(request, 'Loan not found.')
        except Exception as e:
            messages.error(request, f'Error during return: {str(e)}')

    active_loans = Loan.objects.filter(status='active').select_related('user', 'book_copy__book')[:50]
    context = {
        'active_loans': active_loans,
    }
    return render(request, 'circulation/return.html', context)


@login_required
def reserve_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    user = request.user

    # Check if user already has an active reservation for this book
    if Reservation.objects.filter(user=user, book=book, status='active').exists():
        messages.warning(request, 'You already have an active reservation for this book.')
        return redirect('catalog:book_detail', pk=book_id)

    # Check if book is available
    if book.is_available():
        messages.info(request, 'Book is currently available. You can check it out directly.')
        return redirect('catalog:book_detail', pk=book_id)

    # Create reservation
    reservation = Reservation.objects.create(
        user=user,
        book=book,
        expiry_date=timezone.now() + timedelta(days=7)  # Reservation expires in 7 days
    )

    messages.success(request, f'Reservation created for "{book.title}".')
    return redirect('circulation:patron_dashboard')


@login_required
def renew_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, user=request.user, status='active')

    # Check if renewal is allowed (not overdue, within renewal limit)
    if loan.due_date < timezone.now():
        messages.error(request, 'Cannot renew overdue loan.')
        return redirect('circulation:patron_dashboard')

    # Simple renewal: add 14 days
    loan.due_date = loan.due_date + timedelta(days=14)
    loan.save()

    messages.success(request, f'Loan renewed. New due date: {loan.due_date.date()}.')
    return redirect('circulation:patron_dashboard')


@login_required
def pay_fine(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id, loan__user=request.user, status='unpaid')

    # For now, just mark as paid (in real app, integrate with payment gateway)
    fine.status = 'paid'
    fine.paid_date = timezone.now()
    fine.save()

    messages.success(request, f'Fine of ${fine.amount} paid successfully.')
    return redirect('circulation:patron_dashboard')


@login_required
def borrow_book(request, book_id):
    """Allow patrons to request to borrow a book."""
    book = get_object_or_404(Book, id=book_id)
    user = request.user

    # Check if user has unpaid fines
    if Fine.objects.filter(loan__user=user, status='unpaid').exists():
        messages.error(request, 'You have unpaid fines. Please pay your fines before borrowing books.')
        return redirect('circulation:patron_dashboard')

    # Check if user already has an active loan for this book
    if Loan.objects.filter(user=user, book_copy__book=book, status='active').exists():
        messages.warning(request, 'You already have this book on loan.')
        return redirect('catalog:book_detail', pk=book_id)

    # Check if user already has a pending request for this book
    if LoanRequest.objects.filter(user=user, book_copy__book=book, status='pending').exists():
        messages.warning(request, 'You already have a pending borrow request for this book.')
        return redirect('catalog:book_detail', pk=book_id)

    # Find available copies
    available_copies = book.copies.filter(status='available')

    if not available_copies.exists():
        messages.error(request, 'No copies of this book are currently available.')
        return redirect('catalog:book_detail', pk=book_id)

    # For now, just pick the first available copy
    # In a more sophisticated system, we could let users choose specific copies
    book_copy = available_copies.first()

    # Create loan request
    loan_request = LoanRequest.objects.create(
        user=user,
        book_copy=book_copy
    )

    messages.success(request, f'Borrow request submitted for "{book.title}". Staff will review your request shortly.')
    return redirect('circulation:patron_dashboard')


@login_required
def cancel_borrow_request(request, request_id):
    """Allow patrons to cancel their pending borrow requests."""
    loan_request = get_object_or_404(LoanRequest, id=request_id, user=request.user, status='pending')

    loan_request.cancel()
    messages.success(request, 'Borrow request cancelled successfully.')
    return redirect('circulation:patron_dashboard')


@login_required
@user_passes_test(is_staff_user)
def approve_borrow_request(request, request_id):
    """Allow staff to approve borrow requests."""
    loan_request = get_object_or_404(LoanRequest, id=request_id, status='pending')

    try:
        loan = loan_request.approve(request.user)
        messages.success(request, f'Borrow request approved. Book "{loan.book_copy.book.title}" is now on loan to {loan.user.get_full_name()}.')
    except ValueError as e:
        messages.error(request, f'Could not approve request: {e}')

    return redirect('circulation:staff_dashboard')


@login_required
@user_passes_test(is_staff_user)
def reject_borrow_request(request, request_id):
    """Allow staff to reject borrow requests."""
    loan_request = get_object_or_404(LoanRequest, id=request_id, status='pending')

    if request.method == 'POST':
        reason = request.POST.get('reason', 'Request rejected by staff')
        loan_request.reject(reason)
        messages.success(request, 'Borrow request rejected.')
        return redirect('circulation:staff_dashboard')

    context = {
        'loan_request': loan_request,
    }
    return render(request, 'circulation/reject_request.html', context)


@login_required
@user_passes_test(is_staff_user)
def analytics_dashboard(request):
    """Basic analytics dashboard with key metrics."""
    # Time range (default to last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Basic metrics
    total_books = Book.objects.active().count()
    total_users = LibraryUser.objects.count()
    active_loans = Loan.objects.filter(status='active').count()
    overdue_loans = Loan.objects.filter(status='active', due_date__lt=timezone.now()).count()
    total_fines = Fine.objects.filter(status='unpaid').count()

    # Recent activity (last 30 days)
    recent_loans = Loan.objects.filter(created_at__gte=start_date).count()
    recent_returns = Loan.objects.filter(return_date__gte=start_date).count()
    recent_registrations = LibraryUser.objects.filter(date_joined__gte=start_date).count()

    # Popular books (by loans in period)
    popular_books = Book.objects.filter(
        copies__loans__created_at__gte=start_date
    ).annotate(
        loan_count=Count('copies__loans')
    ).order_by('-loan_count')[:10]

    # Most active users
    active_users = LibraryUser.objects.filter(
        loans__created_at__gte=start_date
    ).annotate(
        loan_count=Count('loans')
    ).order_by('-loan_count')[:10]

    context = {
        'total_books': total_books,
        'total_users': total_users,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'total_fines': total_fines,
        'recent_loans': recent_loans,
        'recent_returns': recent_returns,
        'recent_registrations': recent_registrations,
        'popular_books': popular_books,
        'active_users': active_users,
        'days': days,
    }
    return render(request, 'circulation/analytics.html', context)
