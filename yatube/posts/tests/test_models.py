from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )

    def test_models_have_correct_object_names(self):
        group = PostModelTest.group
        group_object_name = group.__str__()
        self.assertEqual(
            group.title,
            group_object_name,
            "Метод __str__ у модели Group не работает корректно",
        )

        post = PostModelTest.post
        post_object_name = post.__str__()
        self.assertEqual(
            post.text[:15],
            post_object_name,
            "Метод __str__ у модели Post не работает корректно",
        )

    def test_verbose_name(self):
        model_verboses = {
            Group: {
                "title": "Название группы",
                "slug": "Уникальный адрес группы",
                "description": "Описание группы"
            },
            Post: {
                "text": "Текст поста",
                "pub_date": "Дата публикации",
                "author": "Автор поста",
                "group": "Группа",
            }
        }

        for model, verboses in model_verboses.items():
            for field, expected_value in verboses.items():
                with self.subTest(field=field):
                    self.assertEqual(
                        model._meta.get_field(field).verbose_name,
                        expected_value,
                        f"verbose name у модели "
                        f"{model.__name__} не работает корректно",
                    )
