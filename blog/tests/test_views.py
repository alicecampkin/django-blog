import datetime
from blog.models import Post
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User


class TestIndexView(TestCase):

    """ Things to test: """
    """ 1. Does the GET request work?"""
    """ 2. Does the context contain a key for 'posts'?"""
    """ 3. Are draft posts excluded? """
    """ 4. Are posts ordered by date (most recent first)? """

    @classmethod
    def setUpTestData(cls):
        u = User.objects.create_user(
            username='user123',
            password='password456'
        )

        Post.objects.create(title='title1', body='body1', author=u, status='draft')

        Post.objects.create(
            title='title2',
            body='body2',
            author=u,
            status='published',
            published=datetime.datetime(2018,1,1)
        )

        Post.objects.create(
            title='title3',
            body='body3',
            author=u,
            status='published',
            published=datetime.datetime(2019,1,1)
        )

        Post.objects.create(
            title='title4',
            body='body4',
            author=u,
            status='published',
            published=datetime.datetime(2020,1,1)
        )

        cls.response = Client().get(reverse('index'))

    def test_get_index(self):
        """ Test that a get request to index works and renders the correct template"""

        self.assertEquals(self.response.status_code, 200)
        self.assertTemplateUsed('blog/index.html')

    def test_context_contains_posts(self):
        """ tests that there the context contains 'posts' """

        self.assertIn('posts', self.response.context)

    def test_excludes_draft_posts(self):
        """ Test that the list of posts on the homepage excludes drafts"""

        number_of_published_posts = len(self.response.context['posts'])

        self.assertEqual(number_of_published_posts, 3)

    def test_posts_are_ordered_by_published_date(self):
        """ Tests that posts are ordered by published date starting with the most recent """
        posts = self.response.context['posts']

        year_post1 = posts[0].published.year
        year_post2 = posts[1].published.year
        year_post3 = posts[2].published.year

        self.assertGreater(year_post1, year_post2)
        self.assertGreater(year_post1, year_post3)
        self.assertGreater(year_post2, year_post3)

class TestAddPostView(TestCase):

    """ Things to test: """
    """ 1. Does the url work?"""
    """ 2. If a user isn't logged in, are they redirected?"""
    """ 3. Are the correct form fields displayed? """
    """ 4. When a post is saved, does it redirect to the preview page? """

    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.url = reverse('add')
        user = User(username='testuser', password='password123')
        user.save()

    def test_get_add(self):
        """ Test that a GET request works and renders the correct template"""

        user = User.objects.get(username='testuser')
        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('blog/add.html')

    def test_user_must_be_logged_in(self):
        """ Test that a non-logged in user is redirected """

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_form_fields(self):
        """ Test that only title and body fields are displayed in the user form"""

        user = User.objects.get(username='testuser')
        self.client.force_login(user)
        response = self.client.get(self.url)
        form = response.context_data['form']

        self.assertEqual(len(form.fields), 2)
        self.assertIn('title', form.fields)
        self.assertIn('body', form.fields)

    def test_success_url(self):
        """ Test that submitting the form redirects to the preview page """

        user = User.objects.get(username='testuser')
        self.client.force_login(user)

        form_data = {
            'title':'my title',
            'body':'This is the post body',
        }
        response = self.client.post(self.url, data=form_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/testuser/my-title/draft')


class TestDraftView(TestCase):
    """ Things to test """
    """ 1. Does the GET request work? """
    """ 2. Does the context include a post? """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='user123',
            password='password456'
        )
        cls.post = Post.objects.create(
            title='my title',
            body='post body',
            author=cls.user
        )
        cls.client = Client()
        cls.url = reverse('draft', args=[cls.user.username, cls.post.slug])
        print(cls.url)

    def test_get_draft(self):
        """ Tests that a GET request works"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('blog/draft.html')

    def test_draft_context(self):
        """ Tests that there's a post included in the context"""
        response = self.client.get(self.url)
        post = response.context['post']

        self.assertEqual(post.title, 'my title')
        self.assertEqual(post.body, 'post body')


class TestEditPostView(TestCase):
    """
    Things to test:
    1. Are non-logged-in users redirected?
    2. Do logged in users receive a 200 status code?
    3. On save, are they redirected to the draft page?
    4. When the title is updated, does the slug update as well?
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username='user123',
            password='password456'
        )
        cls.post = Post.objects.create(
            title='my title',
            body='post body',
            author=cls.user
        )
        cls.client = Client()
        cls.url = '/user123/my-title/edit'

    def test_user_must_be_logged_in(self):
        """ Tests that a non-logged in user is redirected """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_request(self):
        """ Tests that a logged in user receives a 200"""
        user = User.objects.get(username='user123')
        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('blog/edit.html')

    def test_success_url(self):
        """
        Tests that the user is redirected to the draft page on save.
        Tests that the url's slug is correct for an updated title.
        """

        user = User.objects.get(username='user123')
        self.client.force_login(user)

        redirect_url = reverse('draft', args=[user.username, 'new-title'])

        post = {
            'title':'new title',
            'body': 'new bit of text',
            'author': user
        }

        response = self.client.post(self.url, post)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)






