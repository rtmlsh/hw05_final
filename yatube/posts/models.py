from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name="Название группы", max_length=200)
    slug = models.SlugField(
        verbose_name="Уникальный адрес группы", max_length=500, unique=True
    )
    description = models.TextField(verbose_name="Описание группы")

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст поста")
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата публикации"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор поста"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        null=True,
        blank=True,
        verbose_name="Группа",
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост, к которому оставлен комментарий"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария"
    )
    text = models.TextField(verbose_name="Текст комментария")
    created = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата публикации"
    )

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Блогер"
    )

    def __str__(self):
        return f"{self.user} подписан на {self.author}"

    class Meta:
        unique_together = ("user", "author")
