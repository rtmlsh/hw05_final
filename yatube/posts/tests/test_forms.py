import tempfile
import shutil

from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Group, Post, User, Comment
from ..forms import PostForm, CommentForm
from django.urls import reverse
from django.conf import settings

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="TestUser")
        cls.group = Group.objects.create(
            title="testing_form",
            slug="testing_form",
            description="testing_form",
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый пост", group=cls.group
        )
        cls.form = PostForm()
        cls.comment_form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        group = PostFormTests.group
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            "text": "Тестовый пост для проверки формы создания поста",
            "group": group.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:new_post"), data=form_data
        )

        self.assertTrue(Post.objects.filter(
            text=form_data["text"],
            group=group,
            image="posts/small.gif"
        ).exists())
        self.assertRedirects(
            response,
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            )
        )

    def test_update_post(self):
        post = PostFormTests.post
        group = PostFormTests.group
        form_data = {
            "text": f"{post} для проверки формы редактирования поста",
            "group": group.id,
        }
        response = self.authorized_client.post(
            reverse(
                "posts:update_post", kwargs={"post_id": post.pk}
            ),
            data=form_data
        )
        created_post = Post.objects.get(pk=post.pk)

        self.assertEqual(created_post.text, form_data["text"])
        self.assertEqual(created_post.group, group)
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": post.pk})
        )

    def test_comment_post(self):
        form_data = {
            "post": PostFormTests.post,
            "author": PostFormTests.user,
            "text": "Комментарий для проверки формы",
        }

        self.guest_client.post(
            reverse(
                "posts:add_comment", kwargs={"post_id": PostFormTests.post.pk}
            ),
            data=form_data
        )
        self.assertFalse(
            Comment.objects.filter(
                post=form_data["post"],
                author=form_data["author"],
                text=form_data["text"]
            ).exists()
        )

        self.authorized_client.post(
            reverse(
                "posts:add_comment", kwargs={"post_id": PostFormTests.post.pk}
            ),
            data=form_data
        )
        self.assertTrue(
            Comment.objects.filter(
                post=form_data["post"],
                author=form_data["author"],
                text=form_data["text"]
            ).exists()
        )
