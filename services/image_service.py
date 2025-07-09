"""
Image service for fetching Game of Thrones themed images
"""

import aiohttp
import asyncio
import logging
from pathlib import Path
from typing import List, Optional
import hashlib

logger = logging.getLogger(__name__)

class ImageService:
    """Service for fetching relevant images for Game of Thrones content"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = "https://api.unsplash.com"
        self.headers = {
            "Authorization": f"Client-ID {config.unsplash_access_key}",
            "User-Agent": "LoreVideoBot/1.0"
        }
    
    async def get_got_images(self, keywords: List[str]) -> List[str]:
        """
        Fetch relevant images based on Game of Thrones keywords
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of local file paths to downloaded images
        """
        try:
            image_paths = []
            
            # Enhance keywords for better search results
            enhanced_keywords = self._enhance_keywords(keywords)
            
            # Download images for each keyword
            for i, keyword in enumerate(enhanced_keywords[:self.config.image_count]):
                image_path = await self._download_image(keyword, i)
                if image_path:
                    image_paths.append(image_path)
                
                # Rate limiting
                if i < len(enhanced_keywords) - 1:
                    await asyncio.sleep(1)
            
            # Ensure we have enough images
            if len(image_paths) < 3:
                logger.warning("Insufficient images found, using fallback search")
                fallback_images = await self._get_fallback_images(3 - len(image_paths))
                image_paths.extend(fallback_images)
            
            logger.info(f"Downloaded {len(image_paths)} images")
            return image_paths
            
        except Exception as e:
            logger.error(f"Error fetching images: {e}")
            return await self._get_fallback_images(self.config.image_count)
    
    def _enhance_keywords(self, keywords: List[str]) -> List[str]:
        """
        Enhance keywords for better medieval/fantasy image search
        
        Args:
            keywords: Original keywords
            
        Returns:
            Enhanced keywords for better results
        """
        enhancements = {
            'jon snow': 'medieval warrior snow',
            'daenerys': 'medieval queen dragon',
            'tyrion': 'medieval noble castle',
            'arya': 'medieval assassin sword',
            'dragon': 'fantasy dragon fire',
            'winterfell': 'medieval castle snow',
            'kings landing': 'medieval city castle',
            'iron throne': 'medieval throne crown',
            'night king': 'ice warrior fantasy',
            'white walkers': 'ice zombie fantasy',
            'stark': 'medieval wolf heraldry',
            'lannister': 'medieval lion gold',
            'targaryen': 'medieval dragon fire'
        }
        
        enhanced = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in enhancements:
                enhanced.append(enhancements[keyword_lower])
            else:
                # Add fantasy/medieval context to general terms
                enhanced.append(f"medieval fantasy {keyword}")
        
        return enhanced
    
    async def _download_image(self, keyword: str, index: int) -> Optional[str]:
        """
        Download a single image based on keyword
        
        Args:
            keyword: Search keyword
            index: Image index for filename
            
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            # Search for images
            search_url = f"{self.base_url}/search/photos"
            params = {
                "query": keyword,
                "orientation": "portrait",  # Prefer vertical images
                "per_page": 5,
                "order_by": "relevant"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Unsplash API error: {response.status}")
                        return None
                    
                    data = await response.json()
                    results = data.get('results', [])
                    
                    if not results:
                        logger.warning(f"No images found for keyword: {keyword}")
                        return None
                    
                    # Select the best image (first in relevant order)
                    selected_image = results[0]
                    image_url = selected_image['urls']['regular']  # High quality but not huge
                    
                    # Download the image
                    return await self._download_image_file(image_url, keyword, index)
                    
        except Exception as e:
            logger.error(f"Error downloading image for '{keyword}': {e}")
            return None
    
    async def _download_image_file(self, url: str, keyword: str, index: int) -> Optional[str]:
        """
        Download image file from URL
        
        Args:
            url: Image URL
            keyword: Keyword for filename
            index: Image index
            
        Returns:
            Local file path if successful
        """
        try:
            # Create safe filename
            safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_keyword = safe_keyword.replace(' ', '_')
            
            # Create unique filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"image_{index}_{safe_keyword}_{url_hash}.jpg"
            file_path = self.config.temp_dir / filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        logger.info(f"Downloaded image: {filename}")
                        return str(file_path)
                    else:
                        logger.error(f"Failed to download image: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading image file: {e}")
            return None
    
    async def _get_fallback_images(self, count: int) -> List[str]:
        """
        Get fallback Game of Thrones themed images
        
        Args:
            count: Number of fallback images needed
            
        Returns:
            List of fallback image paths
        """
        fallback_keywords = [
            "medieval castle fantasy",
            "medieval sword crown",
            "medieval dragon fire",
            "medieval warrior armor",
            "medieval throne room"
        ]
        
        fallback_images = []
        for i in range(min(count, len(fallback_keywords))):
            image_path = await self._download_image(fallback_keywords[i], f"fallback_{i}")
            if image_path:
                fallback_images.append(image_path)
        
        return fallback_images
    
    def cleanup_images(self, image_paths: List[str]):
        """
        Clean up downloaded image files
        
        Args:
            image_paths: List of image file paths to remove
        """
        for image_path in image_paths:
            try:
                Path(image_path).unlink(missing_ok=True)
                logger.info(f"Cleaned up image: {image_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup image {image_path}: {e}")
