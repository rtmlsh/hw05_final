from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def make_paginator(request, post_list):
    PAGES: int = 10
    paginator = Paginator(post_list, PAGES)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.all()
    page_obj = make_paginator(request, post_list)

    context = {"page_obj": page_obj, "user": request.user}
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts.all().select_related("group")
    page_obj = make_paginator(request, group_list)

    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all().select_related("author")
    page_obj = make_paginator(request, post_list)

    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=user).exists()
    )

    context = {"username": user, "page_obj": page_obj, "following": following}
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()

    context = {
        "post": post,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post_form = form.save(commit=False)
        post_form.author = request.user
        post_form.save()
        return redirect("posts:profile", request.user)

    return render(
        request,
        "posts/create_or_update_post.html",
        {"form": form},
    )


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)

    return render(
        request,
        "posts/create_or_update_post.html",
        {"form": form, "is_edit": is_edit, "post_id": post_id},
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user)
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = make_paginator(request, post_list)

    context = {"page_obj": page_obj, "user": user}

    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if request.user != user:
        Follow.objects.get_or_create(user=request.user, author=user)

    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()

    return redirect("posts:profile", username)
