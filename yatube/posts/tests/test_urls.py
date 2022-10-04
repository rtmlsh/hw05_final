from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Group, Post, User
from django.core.cache import cache

SUCCESS_STATUS = HTTPStatus.OK
BAD_STATUS = HTTPStatus.NOT_FOUND


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="testing",
            slug="testing",
            description="testing",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_exists_for_anonymous(self):
        group = PostURLTests.group
        user = PostURLTests.user
        post = PostURLTests.post
        url_names = [
            "/",
            f"/group/{group.title}/",
            f"/profile/{user}/",
            f"/posts/{post.pk}/",
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, SUCCESS_STATUS)

    def test_unexisting_page(self):
        url_name = "/unexisting_page/"

        response = self.guest_client.get(url_name)
        self.assertEqual(response.status_code, BAD_STATUS)

        response = self.authorized_client.get(url_name)
        self.assertEqual(response.status_code, BAD_STATUS)

        self.assertTemplateUsed(response, "core/404.html")

    def test_authorized(self):
        post = PostURLTests.post
        url_name = f"/posts/{post.pk}/edit/"
        response = self.authorized_client.get(url_name)
        self.assertEqual(response.status_code, SUCCESS_STATUS)

    def test_urls_uses_correct_template(self):
        group = PostURLTests.group
        user = PostURLTests.user
        post = PostURLTests.post
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{group.title}/": "posts/group_list.html",
            f"/profile/{user}/": "posts/profile.html",
            f"/posts/{post.pk}/": "posts/post_detail.html",
            f"/posts/{post.pk}/edit/": "posts/create_or_update_post.html",
            "/create/": "posts/create_or_update_post.html",
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, SUCCESS_STATUS)
                self.assertTemplateUsed(response, template)
