import tempfile
import shutil

from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.urls import reverse
from django import forms
from django.conf import settings

from ..models import Group, Post, User, Follow

POSTS_ON_PAGE: int = 10
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.user = User.objects.create_user(username="TestUser")
        cls.group = Group.objects.create(
            title="testing",
            slug="testing",
            description="testing",
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый пост", image=uploaded
        )
        cls.posts = Post.objects.bulk_create(
            [
                Post(author=cls.user, text="Тестовый пост", image=uploaded)
                for i in range(15)
            ]
        )

        cls.grouped_posts = Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    text="Тестовый пост",
                    group=cls.group,
                    image=uploaded,
                )
                for i in range(12)
            ]
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.user = PostViewsTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        post = PostViewsTests.post
        group = PostViewsTests.group

        templates_pages_names = {
            reverse("posts:posts"): "posts/index.html",
            reverse(
                "posts:group", kwargs={"slug": group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": post.pk}
            ): "posts/post_detail.html",
            reverse("posts:new_post"): "posts/create_or_update_post.html",
            reverse(
                "posts:update_post", kwargs={"post_id": post.pk}
            ): "posts/create_or_update_post.html",
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_index_page(self):
        response = self.authorized_client.get(reverse("posts:posts"))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        post_author = first_object.author
        post_image = first_object.image

        self.assertEqual(len(response.context.get("page_obj")), POSTS_ON_PAGE)
        self.assertEqual(post_text, "Тестовый пост")
        self.assertEqual(post_author, self.user)
        self.assertIsNotNone(post_image)

    def test_context_group_posts_page(self):
        group = PostViewsTests.group
        response = self.authorized_client.get(
            reverse("posts:group", kwargs={"slug": group.slug})
        )
        first_object = response.context["page_obj"][0]
        post_group = first_object.group
        post_image = first_object.image

        self.assertEqual(len(response.context.get("page_obj")), POSTS_ON_PAGE)
        self.assertEqual(post_group, group)
        self.assertIsNotNone(post_image)

    def test_context_profile_posts_page(self):
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
        )
        first_object = response.context["page_obj"][0]
        post_author = first_object.author
        post_image = first_object.image

        self.assertEqual(len(response.context.get("page_obj")), POSTS_ON_PAGE)
        self.assertEqual(post_author, self.user)
        self.assertIsNotNone(post_image)

    def test_context_detail_post_page(self):
        post = PostViewsTests.post
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": post.pk})
        )

        self.assertEqual(response.context.get("post").text, "Тестовый пост")
        self.assertEqual(response.context.get("post").author, self.user)
        self.assertIsNotNone(response.context.get("post").image)

    def test_creating_post(self):
        response = self.authorized_client.post(reverse("posts:new_post"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_updating_post(self):
        post = PostViewsTests.post
        response = self.authorized_client.post(
            reverse("posts:update_post", kwargs={"post_id": post.pk})
        )

        self.assertEqual(response.context["is_edit"], True)
        self.assertEqual(response.context["post_id"], post.pk)

    def test_post_display_on_blog_pages(self):
        group = Group.objects.create(
            title="testing_group",
            slug="testing_group",
            description="testing_group",
        )

        post = Post.objects.create(
            author=self.user,
            text="Тестовый пост для проверки его отображения на страницах",
            group=group,
        )

        response_index_page = (
            self.authorized_client.get(reverse("posts:posts"))
        )
        response_group_page = self.authorized_client.get(
            reverse("posts:group", kwargs={"slug": group.slug})
        )
        response_profile_page = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
        )

        test_post_on_index = response_index_page.context["page_obj"][0]
        test_post_on_group_page = response_group_page.context["page_obj"][0]
        test_post_on_profile_page = (
            response_profile_page.context["page_obj"][0]
        )

        self.assertEqual(test_post_on_index.text, post.text)
        self.assertEqual(test_post_on_group_page.group, group)
        self.assertEqual(test_post_on_profile_page.author, self.user)

    def test_cache_on_main_page(self):
        post = Post.objects.create(
            author=self.user,
            text="Тестовый пост для проверки кэша",
        )
        response = self.authorized_client.get(reverse("posts:posts"))
        post_on_index = response.context["page_obj"][0]

        self.assertEqual(post_on_index, post)

        Post.objects.get(pk=post.pk).delete()
        post_on_index = response.context["page_obj"][0]
        self.assertEqual(post_on_index, post)


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="TestFollower")
        cls.author = User.objects.create(username="TestAuthor")
        cls.another_user = User.objects.create(username="TestAnotherFollower")

    def setUp(self):
        self.user = FollowViewsTests.user
        self.author = FollowViewsTests.author

        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.user)

        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

        self.authorized_another_follower = Client()
        self.authorized_another_follower.force_login(self.another_user)

    def test_follow_author(self):
        self.authorized_follower.get(
            reverse("posts:profile_follow", kwargs={"username": self.author})
        )
        self.authorized_author.get(
            reverse("posts:profile_follow", kwargs={"username": self.author})
        )

        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )
        self.assertEqual(
            Follow.objects.count(), 1
        )

    def test_unfollow_author(self):
        self.authorized_follower.get(
            reverse("posts:profile_unfollow", kwargs={"username": self.author})
        )

        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_follow_feed(self):
        author_post = Post.objects.create(
                author=self.author,
                text="Тестовый пост автора",
        )
        self.authorized_follower.get(
            reverse("posts:profile_follow", kwargs={"username": self.author})
        )
        post_in_user_feed = (
            Follow.objects.get(user=self.user).author.posts.all()
        )

        self.assertTrue(
            post_in_user_feed.filter(text=author_post.text).exists()
        )

    def test_follow_in_right_feed(self):
        user_post = Post.objects.create(
            author=self.user,
            text="Тестовый пост фолловера",
        )
        author_post = Post.objects.create(
            author=self.author,
            text="Тестовый пост автора",
        )

        self.authorized_another_follower.get(
            reverse("posts:profile_follow", kwargs={"username": self.user})
        )
        self.authorized_follower.get(
            reverse("posts:profile_follow", kwargs={"username": self.author})
        )

        post_in_another_user_feed = Follow.objects.get(
            user=self.another_user
        ).author.posts.all()

        self.assertTrue(
            post_in_another_user_feed.filter(text=user_post.text).exists()
        )
        self.assertFalse(
            post_in_another_user_feed.filter(text=author_post.text).exists()
        )
