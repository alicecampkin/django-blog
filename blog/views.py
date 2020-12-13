from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Post
import datetime

def index(request):
    """ Displays a list of posts """

    posts = Post.objects.filter(status='published').order_by('-published')

    context = {
        'page_title':'The POST',
        'posts': posts
    }
    return render(request, 'blog/index.html', context)

@login_required
def draft(request, username, slug):
    """ Provides author with a preview of post in its draft state """

    post = get_object_or_404(Post, author__username=username, slug=slug)

    if request.user != post.author:
        raise Http404("Oops! We couldn't find that page")
    else:
        context = {
            'page_title': post.title,
            'post': post,
        }
        return render(request, 'blog/draft.html', context)

@login_required
def publish_post(request, username, slug):
    """ Changes the status to published and assigns a published date """

    post = get_object_or_404(Post, author__username=username, slug=slug)

    if request.user != post.author:
        raise Http404("Oops! We couldn't find the page you were looking for.")
    else:
        post.status = 'published'
        post.published = datetime.datetime.now()
        post.save()

        redirect_url = reverse('post_detail', args=[username, slug])

        return HttpResponseRedirect(redirect_url)

def post_detail(request, username, slug):
    """
    Displays a post if published.
    If post is draft, user gets a 404, unless they are the author.
    If draft and user is author, then they are redirected to their draft.
    """

    post = get_object_or_404(Post, author__username=username, slug=slug)

    if post.status == 'published':

        context = {
            'page_title': post.title,
            'post': post
        }
        return render(request, 'blog/post_detail.html', context)

    elif request.user == post.author:
        # Redirect author to their draft post
        redirect_url = reverse('draft', args=[username, slug])
        return HttpResponseRedirect(redirect_url)
    else:
        raise Http404("Oops! We couldn't find that post")


class AddPost(LoginRequiredMixin, CreateView):
    """ Allows users to add posts with UI """

    model = Post
    template_name = 'blog/add.html'
    fields = ['title', 'body']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        author = self.object.author
        slug = self.object.slug
        return reverse('draft', args=[author.username, slug])


class EditPost(LoginRequiredMixin, UpdateView):
    """ Allows users to edit posts with UI """

    model = Post
    template_name = 'blog/edit.html'
    fields = ['title', 'body']

    # Make sure posts can only be edited by the author!
    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != self.request.user:
            raise Http404("Oops! We couldn't find that page.")
        return super(EditPost, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        author = self.object.author
        slug = self.object.slug
        return reverse('draft', args=[author.username, slug])


class DeletePost(LoginRequiredMixin, DeleteView):
    """ Allows authors to delete their posts """
    model = Post
    template_name = 'blog/delete.html'
    success_url = reverse_lazy('index')

    # Make sure posts can only be deleted by the author!
    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != self.request.user:
            raise Http404
        return super(DeletePost, self).dispatch(request, *args, **kwargs)