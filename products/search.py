"""
Advanced Search and Filtering System
"""
from django.db.models import Q, Avg, Count, Min, Max
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import Product, Category, Brand
import re


class ProductSearchEngine:
    """Advanced product search engine with AI-powered features"""
    
    def __init__(self):
        self.stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    def search(self, query, filters=None, sort_by='relevance', page=1, per_page=20):
        """
        Advanced search with AI-powered ranking and filtering
        """
        if not query and not filters:
            return Product.objects.filter(is_active=True)
        
        # Start with active products
        queryset = Product.objects.filter(is_active=True)
        
        # Apply text search
        if query:
            queryset = self._apply_text_search(queryset, query)
        
        # Apply filters
        if filters:
            queryset = self._apply_filters(queryset, filters)
        
        # Apply sorting
        queryset = self._apply_sorting(queryset, sort_by, query)
        
        # Add annotations for enhanced data
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews'),
            sales_rank=Count('orderitem')
        ).select_related('category', 'brand').prefetch_related('images', 'reviews')
        
        return queryset
    
    def _apply_text_search(self, queryset, query):
        """Apply intelligent text search"""
        # Clean and process query
        cleaned_query = self._clean_query(query)
        search_terms = self._extract_search_terms(cleaned_query)
        
        # Multi-field search with weighted relevance
        search_q = Q()
        
        for term in search_terms:
            # Exact matches get highest priority
            search_q |= (
                Q(name__icontains=term) |
                Q(description__icontains=term) |
                Q(short_description__icontains=term) |
                Q(tags__icontains=term) |
                Q(category__name__icontains=term) |
                Q(brand__name__icontains=term) |
                Q(sku__icontains=term)
            )
        
        return queryset.filter(search_q).distinct()
    
    def _apply_filters(self, queryset, filters):
        """Apply advanced filtering"""
        if 'category' in filters:
            if isinstance(filters['category'], list):
                queryset = queryset.filter(category__slug__in=filters['category'])
            else:
                queryset = queryset.filter(category__slug=filters['category'])
        
        if 'brand' in filters:
            if isinstance(filters['brand'], list):
                queryset = queryset.filter(brand__slug__in=filters['brand'])
            else:
                queryset = queryset.filter(brand__slug=filters['brand'])
        
        if 'price_min' in filters:
            queryset = queryset.filter(price__gte=filters['price_min'])
        
        if 'price_max' in filters:
            queryset = queryset.filter(price__lte=filters['price_max'])
        
        if 'rating_min' in filters:
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=filters['rating_min'])
        
        if 'in_stock' in filters and filters['in_stock']:
            queryset = queryset.filter(stock__gt=0)
        
        if 'on_sale' in filters and filters['on_sale']:
            queryset = queryset.filter(compare_price__isnull=False, compare_price__gt=0)
        
        if 'featured' in filters and filters['featured']:
            queryset = queryset.filter(is_featured=True)
        
        if 'currency' in filters:
            queryset = queryset.filter(currency=filters['currency'])
        
        return queryset
    
    def _apply_sorting(self, queryset, sort_by, query=None):
        """Apply intelligent sorting"""
        if sort_by == 'relevance' and query:
            # AI-powered relevance scoring
            return queryset.order_by('-is_featured', '-views_count', '-sales_count')
        elif sort_by == 'price_low':
            return queryset.order_by('price')
        elif sort_by == 'price_high':
            return queryset.order_by('-price')
        elif sort_by == 'rating':
            return queryset.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating', '-review_count')
        elif sort_by == 'newest':
            return queryset.order_by('-created_at')
        elif sort_by == 'bestseller':
            return queryset.order_by('-sales_count', '-views_count')
        elif sort_by == 'name':
            return queryset.order_by('name')
        else:
            return queryset.order_by('-is_featured', '-created_at')
    
    def _clean_query(self, query):
        """Clean and normalize search query"""
        # Remove special characters and normalize
        cleaned = re.sub(r'[^\w\s]', ' ', query.lower())
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    def _extract_search_terms(self, query):
        """Extract meaningful search terms"""
        words = query.split()
        # Remove stopwords
        terms = [word for word in words if word not in self.stopwords and len(word) > 2]
        return terms
    
    def get_search_suggestions(self, query, limit=10):
        """Get AI-powered search suggestions"""
        if len(query) < 2:
            return []
        
        suggestions = []
        
        # Product name suggestions
        products = Product.objects.filter(
            name__icontains=query, is_active=True
        ).values_list('name', flat=True)[:limit//2]
        suggestions.extend(products)
        
        # Category suggestions
        categories = Category.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:limit//4]
        suggestions.extend(categories)
        
        # Brand suggestions
        brands = Brand.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:limit//4]
        suggestions.extend(brands)
        
        return list(set(suggestions))[:limit]
    
    def get_filter_options(self, query=None, current_filters=None):
        """Get dynamic filter options based on current search"""
        base_queryset = Product.objects.filter(is_active=True)
        
        if query:
            base_queryset = self._apply_text_search(base_queryset, query)
        
        if current_filters:
            # Apply all filters except the one we're calculating options for
            base_queryset = self._apply_filters(base_queryset, current_filters)
        
        # Get available categories
        categories = Category.objects.filter(
            products__in=base_queryset
        ).annotate(
            product_count=Count('products')
        ).order_by('-product_count', 'name')
        
        # Get available brands
        brands = Brand.objects.filter(
            products__in=base_queryset
        ).annotate(
            product_count=Count('products')
        ).order_by('-product_count', 'name')
        
        # Get price range
        price_range = base_queryset.aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        
        return {
            'categories': categories,
            'brands': brands,
            'price_range': price_range,
        }


class SearchAnalytics:
    """Track and analyze search behavior"""
    
    @staticmethod
    def track_search(query, user=None, results_count=0, filters=None):
        """Track search queries for analytics"""
        from analytics.models import SearchQuery as SearchQueryModel
        
        SearchQueryModel.objects.create(
            query=query,
            user=user if user and user.is_authenticated else None,
            results_count=results_count,
            filters=filters or {},
            ip_address=None,  # Add IP tracking if needed
        )
    
    @staticmethod
    def get_trending_searches(days=7, limit=10):
        """Get trending search queries"""
        from django.utils import timezone
        from datetime import timedelta
        from analytics.models import SearchQuery as SearchQueryModel
        
        since = timezone.now() - timedelta(days=days)
        
        return SearchQueryModel.objects.filter(
            created_at__gte=since
        ).values('query').annotate(
            search_count=Count('id')
        ).order_by('-search_count')[:limit]
    
    @staticmethod
    def get_zero_result_searches(days=7):
        """Get searches that returned no results"""
        from django.utils import timezone
        from datetime import timedelta
        from analytics.models import SearchQuery as SearchQueryModel
        
        since = timezone.now() - timedelta(days=days)
        
        return SearchQueryModel.objects.filter(
            created_at__gte=since,
            results_count=0
        ).values('query').annotate(
            search_count=Count('id')
        ).order_by('-search_count')
