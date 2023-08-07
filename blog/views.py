from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count, Prefetch

    
def serialize_post(post):
    tags = list(post.tags.all())
    first_tag_title = tags[0].title if tags else None
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments.count(),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': first_tag_title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_with_tag,
    }


def index(request):
    tags_prefetch = Prefetch('tags', queryset=Tag.objects.annotate(posts_with_tag=Count('posts')).order_by('title'))
    most_popular_posts = Post.objects.popular().prefetch_related(tags_prefetch).fetch_with_comments_count()[:5]

    post_ids = [post.id for post in most_popular_posts]

    posts_with_tags = Post.objects.filter(id__in=post_ids)
    
    posts_with_tags = posts_with_tags.prefetch_related(tags_prefetch)

    serialized_posts = [
        serialize_post(post) for post in most_popular_posts
    ]

    popular_tags = Tag.objects.popular()[:5]

    context = {
        'most_popular_posts': serialized_posts,
        'popular_tags': [serialize_tag(tag) for tag in popular_tags],
    }

    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.select_related('author').prefetch_related(
        'comments',
        Prefetch('tags', queryset=Tag.objects.order_by('title'))
    ).get(slug=slug)

    likes = post.likes.count()

    # Теги уже загружены с помощью Prefetch, поэтому просто преобразуем их в список
    tags = list(post.tags.all())

    # Используем prefetch_related для комментариев, чтобы избежать дополнительного запроса
    comments = list(post.comments.all().values('text', 'published_at', 'author__username'))

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': comments,
        'likes_amount': likes,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in tags],
    }

    popular_tags = Tag.objects.popular()[:5]

    most_popular_posts = Post.objects.popular()[:5].prefetch_related(
        Prefetch('tags', queryset=Tag.objects.order_by('title'))
    )

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }

    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    related_posts = Post.objects.filter(tags__id=tag.id).prefetch_related(
        Prefetch('tags', queryset=Tag.objects.order_by('title')),
        Prefetch('comments', queryset=Comment.objects.annotate(comments_count=Count('id')))
    ).select_related('author')

    serialized_posts = [
        {
            'title': post.title,
            'teaser_text': post.text[:200],
            'author': post.author.username,
            'comments_amount': getattr(post, 'comments_count', 0),
            'image_url': post.image.url if post.image else None,
            'published_at': post.published_at,
            'slug': post.slug,
            'tags': [serialize_tag(tag) for tag in post.tags.all()],
            'first_tag_title': post.tags.first().title if post.tags.exists() else None,
        }
        for post in related_posts
    ]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in Tag.objects.popular()[:5]],
        'posts': serialized_posts,
        'most_popular_posts': [
            serialize_post(post) for post in Post.objects.popular()[:5].prefetch_related(
                Prefetch('tags', queryset=Tag.objects.order_by('title')),
                Prefetch('comments', queryset=Comment.objects.annotate(comments_count=Count('id')))
            ).select_related('author')
        ],
    }

    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
