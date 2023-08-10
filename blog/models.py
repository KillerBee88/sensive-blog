from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class TagQuerySet(models.QuerySet):

    def popular(self):
        return self.annotate(posts_count=models.Count('posts')) \
                   .order_by('-posts_count')


class PostQuerySet(models.QuerySet):

    def popular(self):
        return self.annotate(likes_count=models.Count('likes', distinct=True))\
                   .order_by('-likes_count')

    def fetch_with_comments_count(self):
        """
        Функция fetch_with_comments_count возвращает список постов с предварительно загруженными комментариями,
        вместо использования annotate для аннотации количества комментариев.
        """
        posts_ids = [post.id for post in self]
        posts_with_comments = Post.objects \
                                  .filter(id__in=posts_ids) \
                                  .annotate(comments_count=models.Count('comments'))

        ids_and_comments = posts_with_comments.values_list('id', 'comments_count')
        count_for_id = dict(ids_and_comments)
        for post in self:
            post.comments_count = count_for_id[post.id]
        return self

    def fetch_with_tags(self):
        tags = models.Prefetch('tags', queryset=Tag.objects.annotate(posts_count=models.Count('posts')))
        return self.prefetch_related(tags)


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

    objects = TagQuerySet.as_manager()

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост, к которому написан')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'