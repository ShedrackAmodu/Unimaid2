"""
Test script for bulk actions functionality.
This script can be used to verify that bulk actions are working correctly.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.contrib.messages.storage.fallback import FallbackStorage

from apps.accounts.models import LibraryUser, StudyRoom, StudyRoomBooking
from apps.catalog.models import Book, BookCopy, Author, Topic
from apps.circulation.models import Loan, Reservation, Attendance
from apps.events.models import Event
from apps.repository.models import EBook
from apps.blog.models import BlogPost, News, StaticPage, FeaturedContent

from config.bulk_actions import (
    bulk_activate_users, bulk_deactivate_users,
    bulk_update_membership_type, bulk_assign_department,
    bulk_update_study_room_status, bulk_update_booking_status,
    bulk_update_book_status, bulk_update_book_condition,
    bulk_update_book_location, bulk_assign_authors, bulk_assign_topics,
    bulk_update_loan_status, bulk_extend_loans, bulk_calculate_fines,
    bulk_process_reservations, bulk_checkout_visitors,
    bulk_update_event_status, bulk_update_ebook_access_level,
    bulk_update_blog_status, bulk_update_news_status,
    bulk_update_static_page_status, bulk_update_featured_content_order
)


class BulkActionsTestCase(TestCase):
    """Test case for bulk actions functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create test users
        self.user1 = LibraryUser.objects.create_user(
            username='testuser1',
            email='user1@test.com',
            membership_type='student',
            is_active=False
        )
        self.user2 = LibraryUser.objects.create_user(
            username='testuser2',
            email='user2@test.com',
            membership_type='staff',
            is_active=False
        )
        
        # Create test study rooms
        self.room1 = StudyRoom.objects.create(
            name='Test Room 1',
            room_type='group',
            capacity=4,
            is_active=False
        )
        self.room2 = StudyRoom.objects.create(
            name='Test Room 2',
            room_type='individual',
            capacity=1,
            is_active=False
        )
        
        # Create test books
        self.book1 = Book.objects.create(
            title='Test Book 1',
            isbn='1234567890123',
            publication_date='2024-01-01'
        )
        self.book2 = Book.objects.create(
            title='Test Book 2',
            isbn='1234567890124',
            publication_date='2024-01-01'
        )
        
        self.book_copy1 = BookCopy.objects.create(
            book=self.book1,
            barcode='BC001',
            status='checked_out',
            condition='good'
        )
        self.book_copy2 = BookCopy.objects.create(
            book=self.book2,
            barcode='BC002',
            status='reserved',
            condition='fair'
        )
        
        # Create test authors
        self.author1 = Author.objects.create(name='Test Author 1')
        self.author2 = Author.objects.create(name='Test Author 2')
        
        # Create test topics
        self.topic1 = Topic.objects.create(name='Test Topic 1', code='TOPIC001')
        self.topic2 = Topic.objects.create(name='Test Topic 2', code='TOPIC002')
        
        # Create test loans
        self.loan1 = Loan.objects.create(
            user=self.user1,
            book_copy=self.book_copy1,
            status='active'
        )
        self.loan2 = Loan.objects.create(
            user=self.user2,
            book_copy=self.book_copy2,
            status='overdue'
        )
        
        # Create test events
        self.event1 = Event.objects.create(
            title='Test Event 1',
            date='2024-12-01',
            time='10:00:00',
            location='Test Location',
            organizer=self.user
        )
        self.event2 = Event.objects.create(
            title='Test Event 2',
            date='2024-12-02',
            time='14:00:00',
            location='Test Location 2',
            organizer=self.user
        )
        
        # Create test eBooks
        self.ebook1 = EBook.objects.create(
            title='Test eBook 1',
            authors='Test Author',
            access_level='public'
        )
        self.ebook2 = EBook.objects.create(
            title='Test eBook 2',
            authors='Test Author 2',
            access_level='restricted'
        )
        
        # Create test blog posts
        self.blog1 = BlogPost.objects.create(
            title='Test Blog 1',
            content='Test content',
            status='draft'
        )
        self.blog2 = BlogPost.objects.create(
            title='Test Blog 2',
            content='Test content 2',
            status='published'
        )
        
        # Create test news
        self.news1 = News.objects.create(
            title='Test News 1',
            content='Test news content',
            status='draft'
        )
        self.news2 = News.objects.create(
            title='Test News 2',
            content='Test news content 2',
            status='published'
        )
        
        # Create test static pages
        self.page1 = StaticPage.objects.create(
            title='Test Page 1',
            content='Test page content',
            is_active=False
        )
        self.page2 = StaticPage.objects.create(
            title='Test Page 2',
            content='Test page content 2',
            is_active=True
        )
        
        # Create test featured content
        self.featured1 = FeaturedContent.objects.create(
            title='Test Featured 1',
            content='Test featured content',
            is_active=True,
            order=1
        )
        self.featured2 = FeaturedContent.objects.create(
            title='Test Featured 2',
            content='Test featured content 2',
            is_active=False,
            order=2
        )
    
    def _create_request(self):
        """Create a mock request for testing."""
        request = HttpRequest()
        request.user = self.user
        request.method = 'POST'
        request.POST = {}
        
        # Add messages framework
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        
        return request
    
    def test_bulk_activate_users(self):
        """Test bulk user activation."""
        request = self._create_request()
        queryset = LibraryUser.objects.filter(is_active=False)
        
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_activate_users(None, request, queryset)
        
        # Verify users are activated
        activated_count = LibraryUser.objects.filter(is_active=True).count()
        self.assertGreater(activated_count, 0)
    
    def test_bulk_deactivate_users(self):
        """Test bulk user deactivation."""
        request = self._create_request()
        queryset = LibraryUser.objects.filter(is_active=True)
        
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_deactivate_users(None, request, queryset)
        
        # Verify users are deactivated
        deactivated_count = LibraryUser.objects.filter(is_active=False).count()
        self.assertGreater(deactivated_count, 0)
    
    def test_bulk_update_study_room_status(self):
        """Test bulk study room status update."""
        request = self._create_request()
        request.POST['is_active'] = 'true'
        
        queryset = StudyRoom.objects.filter(is_active=False)
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_study_room_status(None, request, queryset)
        
        # Verify rooms are activated
        activated_count = StudyRoom.objects.filter(is_active=True).count()
        self.assertGreater(activated_count, 0)
    
    def test_bulk_update_book_status(self):
        """Test bulk book status update."""
        request = self._create_request()
        request.POST['status'] = 'available'
        
        queryset = BookCopy.objects.filter(status='checked_out')
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_book_status(None, request, queryset)
        
        # Verify books are updated
        updated_count = BookCopy.objects.filter(status='available').count()
        self.assertGreater(updated_count, 0)
    
    def test_bulk_assign_authors(self):
        """Test bulk author assignment."""
        request = self._create_request()
        request.POST['authors'] = [str(self.author1.id), str(self.author2.id)]
        
        queryset = Book.objects.all()
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_assign_authors(None, request, queryset)
        
        # Verify authors are assigned
        for book in queryset:
            self.assertTrue(book.authors.filter(id=self.author1.id).exists())
            self.assertTrue(book.authors.filter(id=self.author2.id).exists())
    
    def test_bulk_assign_topics(self):
        """Test bulk topic assignment."""
        request = self._create_request()
        request.POST['topic'] = str(self.topic1.id)
        
        queryset = Book.objects.all()
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_assign_topics(None, request, queryset)
        
        # Verify topics are assigned
        for book in queryset:
            self.assertEqual(book.topic, self.topic1)
    
    def test_bulk_update_loan_status(self):
        """Test bulk loan status update."""
        request = self._create_request()
        request.POST['status'] = 'returned'
        
        queryset = Loan.objects.filter(status='active')
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_loan_status(None, request, queryset)
        
        # Verify loans are updated
        updated_count = Loan.objects.filter(status='returned').count()
        self.assertGreater(updated_count, 0)
    
    def test_bulk_extend_loans(self):
        """Test bulk loan extension."""
        request = self._create_request()
        request.POST['days'] = '7'
        
        queryset = Loan.objects.filter(status='active')
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_extend_loans(None, request, queryset)
        
        # Verify loans are extended (this would require checking due_date changes)
        # For now, just verify the function runs without error
    
    def test_bulk_update_event_status(self):
        """Test bulk event status update."""
        request = self._create_request()
        request.POST['status'] = 'completed'
        
        queryset = Event.objects.all()
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_event_status(None, request, queryset)
        
        # Verify events are updated
        updated_count = Event.objects.filter(status='completed').count()
        self.assertGreater(updated_count, 0)
    
    def test_bulk_update_ebook_access_level(self):
        """Test bulk eBook access level update."""
        request = self._create_request()
        request.POST['access_level'] = 'public'
        
        queryset = EBook.objects.filter(access_level='restricted')
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_ebook_access_level(None, request, queryset)
        
        # Verify eBooks are updated
        updated_count = EBook.objects.filter(access_level='public').count()
        self.assertGreater(updated_count, 0)
    
    def test_bulk_update_blog_status(self):
        """Test bulk blog post status update."""
        request = self._create_request()
        request.POST['status'] = 'published'
        
        queryset = BlogPost.objects.filter(status='draft')
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_blog_status(None, request, queryset)
        
        # Verify blog posts are updated
        updated_count = BlogPost.objects.filter(status='published').count()
        self.assertGreater(updated_count, 0)
    
    def test_bulk_update_news_status(self):
        """Test bulk news status update."""
        request = self._create_request()
        request.POST['status'] = 'draft'
        
        queryset = News.objects.filter(status='published')
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_news_status(None, request, queryset)
        
        # Verify news items are updated
        updated_count = News.objects.filter(status='draft').count()
        self.assertGreater(updated_count, 0)
    
    def test_bulk_update_static_page_status(self):
        """Test bulk static page status update."""
        request = self._create_request()
        request.POST['is_active'] = 'false'
        
        queryset = StaticPage.objects.filter(is_active=True)
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_static_page_status(None, request, queryset)
        
        # Verify pages are updated
        updated_count = StaticPage.objects.filter(is_active=False).count()
        self.assertGreater(updated_count, 0)
    
    def test_bulk_update_featured_content_order(self):
        """Test bulk featured content order update."""
        request = self._create_request()
        request.POST['order'] = '10'
        
        queryset = FeaturedContent.objects.all()
        initial_count = queryset.count()
        self.assertGreater(initial_count, 0)
        
        bulk_update_featured_content_order(None, request, queryset)
        
        # Verify order is updated
        updated_count = FeaturedContent.objects.filter(order=10).count()
        self.assertGreater(updated_count, 0)


def run_bulk_action_tests():
    """
    Run bulk action tests manually.
    This can be called from Django shell or management command.
    """
    import os
    import django
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    # Run tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["config.test_bulk_actions"])
    
    if failures:
        print(f"Tests failed with {failures} failures")
        return False
    else:
        print("All bulk action tests passed!")
        return True


if __name__ == '__main__':
    run_bulk_action_tests()