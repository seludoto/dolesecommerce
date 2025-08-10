"""
AI-Powered Recommendation Engine
"""
import numpy as np
from django.db.models import Count, Avg, Q
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import json


class RecommendationEngine:
    """Advanced AI-powered recommendation system"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
        self.min_interactions = 3
        self.similarity_threshold = 0.3
    
    def get_recommendations_for_user(self, user, limit=10, algorithm='hybrid'):
        """Get personalized recommendations for a user"""
        if not user or not user.is_authenticated:
            return self.get_trending_products(limit)
        
        cache_key = f'user_recommendations_{user.id}_{algorithm}_{limit}'
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            if algorithm == 'collaborative':
                recommendations = self._collaborative_filtering(user, limit)
            elif algorithm == 'content':
                recommendations = self._content_based_filtering(user, limit)
            elif algorithm == 'hybrid':
                recommendations = self._hybrid_recommendations(user, limit)
            else:
                recommendations = self.get_trending_products(limit)
            
            cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations
    
    def get_product_recommendations(self, product, limit=8):
        """Get products similar to the given product"""
        cache_key = f'product_recommendations_{product.id}_{limit}'
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            recommendations = self._product_similarity_recommendations(product, limit)
            cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations
    
    def get_trending_products(self, limit=10, days=7):
        """Get trending products based on recent activity"""
        from products.models import Product
        
        cache_key = f'trending_products_{limit}_{days}'
        trending = cache.get(cache_key)
        
        if trending is None:
            since = timezone.now() - timedelta(days=days)
            
            trending = Product.objects.filter(
                is_active=True,
                created_at__gte=since - timedelta(days=30)  # Not too old
            ).annotate(
                recent_views=Count('viewed_by', filter=Q(viewed_by__viewed_at__gte=since))
            ).filter(
                Q(recent_views__gt=0) | Q(views_count__gt=0)
            ).order_by(
                '-recent_views',
                '-views_count',
                '-sales_count'
            )[:limit]
            
            cache.set(cache_key, trending, self.cache_timeout)
        
        return trending
    
    def get_category_recommendations(self, category, limit=8):
        """Get recommended products for a category"""
        from products.models import Product
        
        return Product.objects.filter(
            category=category,
            is_active=True
        ).annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by(
            '-is_featured',
            '-avg_rating',
            '-views_count'
        )[:limit]
    
    def get_frequently_bought_together(self, product, limit=5):
        """Get products frequently bought together with the given product"""
        from products.models import Product
        
        cache_key = f'bought_together_{product.id}_{limit}'
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            try:
                from orders.models import OrderItem
                
                # Find orders that contain this product
                orders_with_product = OrderItem.objects.filter(
                    product=product
                ).values_list('order_id', flat=True)
                
                # Find other products in those orders
                related_products = OrderItem.objects.filter(
                    order_id__in=orders_with_product
                ).exclude(
                    product=product
                ).values('product').annotate(
                    frequency=Count('product')
                ).order_by('-frequency')[:limit]
                
                product_ids = [item['product'] for item in related_products]
                recommendations = Product.objects.filter(
                    id__in=product_ids,
                    is_active=True
                )
            except:
                recommendations = Product.objects.none()
            
            cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations
    
    def get_customers_also_viewed(self, product, limit=8):
        """Get products that customers also viewed"""
        from products.models import Product
        
        cache_key = f'also_viewed_{product.id}_{limit}'
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            try:
                # Get users who viewed this product
                users_who_viewed = product.viewed_by.values_list('user_id', flat=True)
                
                # Get other products viewed by these users
                related_products = Product.objects.filter(
                    viewed_by__user_id__in=users_who_viewed,
                    is_active=True
                ).exclude(
                    id=product.id
                ).annotate(
                    view_count=Count('viewed_by')
                ).order_by('-view_count', '-views_count')[:limit]
                
                recommendations = related_products
            except:
                recommendations = Product.objects.filter(
                    category=product.category,
                    is_active=True
                ).exclude(id=product.id)[:limit]
            
            cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations
    
    def _collaborative_filtering(self, user, limit):
        """Collaborative filtering based on user behavior"""
        try:
            from orders.models import OrderItem
            
            # Get user's purchase history
            user_purchases = OrderItem.objects.filter(
                order__user=user
            ).values_list('product_id', flat=True)
            
            if not user_purchases:
                return self.get_trending_products(limit)
            
            # Find similar users based on purchase history
            similar_users = User.objects.filter(
                orders__items__product_id__in=user_purchases
            ).exclude(id=user.id).annotate(
                common_purchases=Count('orders__items__product')
            ).filter(
                common_purchases__gte=self.min_interactions
            ).order_by('-common_purchases')[:20]
            
            # Get products purchased by similar users
            from products.models import Product
            recommended_products = Product.objects.filter(
                orderitem__order__user__in=similar_users,
                is_active=True
            ).exclude(
                id__in=user_purchases
            ).annotate(
                recommendation_score=Count('orderitem')
            ).order_by('-recommendation_score')[:limit]
            
            return recommended_products
        except:
            return self.get_trending_products(limit)
    
    def _content_based_filtering(self, user, limit):
        """Content-based filtering using product features"""
        try:
            from products.models import Product
            from orders.models import OrderItem
            
            # Get user's purchase and view history
            user_products = list(OrderItem.objects.filter(
                order__user=user
            ).values_list('product_id', flat=True))
            
            # Add recently viewed products
            if hasattr(user, 'recently_viewed'):
                viewed_products = list(user.recently_viewed.values_list('product_id', flat=True)[:10])
                user_products.extend(viewed_products)
            
            if not user_products:
                return self.get_trending_products(limit)
            
            # Get categories and brands user is interested in
            user_categories = Product.objects.filter(
                id__in=user_products
            ).values_list('category_id', flat=True)
            
            user_brands = Product.objects.filter(
                id__in=user_products
            ).values_list('brand_id', flat=True)
            
            # Find similar products
            recommendations = Product.objects.filter(
                Q(category_id__in=user_categories) | Q(brand_id__in=user_brands),
                is_active=True
            ).exclude(
                id__in=user_products
            ).annotate(
                avg_rating=Avg('reviews__rating'),
                similarity_score=Count('category') + Count('brand')
            ).order_by(
                '-similarity_score',
                '-avg_rating',
                '-views_count'
            )[:limit]
            
            return recommendations
        except:
            return self.get_trending_products(limit)
    
    def _hybrid_recommendations(self, user, limit):
        """Hybrid approach combining multiple algorithms"""
        # Get recommendations from different algorithms
        collaborative = list(self._collaborative_filtering(user, limit // 2))
        content_based = list(self._content_based_filtering(user, limit // 2))
        trending = list(self.get_trending_products(limit // 4))
        
        # Combine and deduplicate
        all_recommendations = collaborative + content_based + trending
        seen_ids = set()
        unique_recommendations = []
        
        for product in all_recommendations:
            if product.id not in seen_ids:
                unique_recommendations.append(product)
                seen_ids.add(product.id)
                if len(unique_recommendations) >= limit:
                    break
        
        return unique_recommendations
    
    def _product_similarity_recommendations(self, product, limit):
        """Find products similar to the given product"""
        from products.models import Product
        
        # Same category products
        category_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)
        
        # Same brand products
        brand_products = Product.objects.filter(
            brand=product.brand,
            is_active=True
        ).exclude(id=product.id) if product.brand else Product.objects.none()
        
        # Price range similarity
        price_range = product.price * 0.3  # 30% price variance
        price_similar = Product.objects.filter(
            price__gte=product.price - price_range,
            price__lte=product.price + price_range,
            is_active=True
        ).exclude(id=product.id)
        
        # Combine with weighted scoring
        similar_products = (category_products | brand_products | price_similar).distinct().annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).order_by(
            '-avg_rating',
            '-review_count',
            '-views_count'
        )[:limit]
        
        return similar_products
    
    def track_user_interaction(self, user, product, interaction_type):
        """Track user interactions for improving recommendations"""
        if not user or not user.is_authenticated:
            return
        
        try:
            from analytics.models import UserInteraction
            
            UserInteraction.objects.create(
                user=user,
                product=product,
                interaction_type=interaction_type,
                timestamp=timezone.now()
            )
            
            # Invalidate user's recommendation cache
            cache_patterns = [
                f'user_recommendations_{user.id}_*',
                f'trending_products_*',
            ]
            
            for pattern in cache_patterns:
                try:
                    cache.delete(pattern)
                except:
                    pass
        except:
            pass


class PersonalizationEngine:
    """Advanced personalization features"""
    
    @staticmethod
    def get_personalized_homepage(user):
        """Get personalized homepage content"""
        if not user or not user.is_authenticated:
            return PersonalizationEngine._get_default_homepage()
        
        cache_key = f'personalized_homepage_{user.id}'
        content = cache.get(cache_key)
        
        if content is None:
            rec_engine = RecommendationEngine()
            
            content = {
                'featured_products': rec_engine.get_recommendations_for_user(user, 8),
                'trending_products': rec_engine.get_trending_products(6),
                'recommended_categories': PersonalizationEngine._get_recommended_categories(user),
                'recent_views': getattr(user, 'recently_viewed', [])[:6] if hasattr(user, 'recently_viewed') else [],
                'wishlist_items': getattr(user, 'wishlists', [])[:4] if hasattr(user, 'wishlists') else [],
            }
            
            cache.set(cache_key, content, 1800)  # 30 minutes
        
        return content
    
    @staticmethod
    def _get_default_homepage():
        """Get default homepage for anonymous users"""
        from products.models import Product, Category
        
        return {
            'featured_products': Product.objects.filter(is_featured=True, is_active=True)[:8],
            'trending_products': Product.objects.filter(is_active=True).order_by('-views_count')[:6],
            'recommended_categories': Category.objects.filter(is_featured=True)[:6],
            'recent_views': [],
            'wishlist_items': [],
        }
    
    @staticmethod
    def _get_recommended_categories(user):
        """Get categories recommended for the user"""
        try:
            from products.models import Category
            
            # Get user's purchase history categories
            user_categories = Category.objects.filter(
                products__orderitem__order__user=user
            ).annotate(
                purchase_count=Count('products__orderitem')
            ).order_by('-purchase_count')[:3]
            
            # Get trending categories
            trending_categories = Category.objects.filter(
                is_featured=True
            )[:3]
            
            # Combine and deduplicate
            all_categories = list(user_categories) + list(trending_categories)
            seen_ids = set()
            unique_categories = []
            
            for category in all_categories:
                if category.id not in seen_ids:
                    unique_categories.append(category)
                    seen_ids.add(category.id)
                    if len(unique_categories) >= 6:
                        break
            
            return unique_categories
        except:
            from products.models import Category
            return Category.objects.filter(is_featured=True)[:6]
