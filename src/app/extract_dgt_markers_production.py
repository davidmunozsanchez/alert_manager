"""
Production-ready DGT traffic markers extractor.
Extracts all traffic markers from the DGT eTraffic map and prepares data for database insertion.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TrafficMarker:
    """Traffic marker data structure."""
    id: str
    title: str
    description: str
    latitude: float
    longitude: float
    road_type: Optional[str]
    cause: Optional[str]
    severity: Optional[str]
    full_text: str
    extracted_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DGTMarkerExtractor:
    """Extract traffic markers from DGT eTraffic map."""
    
    BASE_URL = "https://etraffic.dgt.es/etrafficWEB/"
    
    def __init__(self):
        self.markers: List[TrafficMarker] = []
        self.extraction_errors: List[str] = []
    
    async def extract_all_markers(self) -> List[TrafficMarker]:
        """Extract all traffic markers from the map."""
        logger.info("=" * 80)
        logger.info("DGT TRAFFIC MARKERS EXTRACTION - PRODUCTION (OPTIMIZED)")
        logger.info("=" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.set_default_timeout(60000)
            
            logger.info(f"\nLoading page: {self.BASE_URL}")
            try:
                await page.goto(self.BASE_URL, wait_until="load")
                logger.info("✓ Page loaded")
            except Exception as e:
                logger.error(f"✗ Failed to load page: {e}")
                await browser.close()
                return []
            
            await page.wait_for_timeout(2000)
            
            # Extract all markers using optimized JavaScript
            logger.info("\nExtracting all markers via JavaScript...")
            markers_data = await self._extract_markers_javascript(page)
            
            # Convert extracted data to TrafficMarker objects
            for i, marker_data in enumerate(markers_data):
                try:
                    marker = TrafficMarker(
                        id=marker_data.get('id', f"dgt_{i}"),
                        title=marker_data.get('title', 'Unknown'),
                        description=marker_data.get('description', ''),
                        latitude=marker_data.get('latitude', 0.0),
                        longitude=marker_data.get('longitude', 0.0),
                        road_type=marker_data.get('road_type'),
                        cause=marker_data.get('cause'),
                        severity=marker_data.get('severity'),
                        full_text=marker_data.get('full_text', ''),
                        extracted_at=datetime.now().isoformat(),
                    )
                    self.markers.append(marker)
                    logger.info(f"✓ Extracted {i+1}/{len(markers_data)}: {marker.title[:40]}")
                    
                except Exception as e:
                    error_msg = f"Error converting marker {i}: {e}"
                    logger.warning(f"✗ {error_msg}")
                    self.extraction_errors.append(error_msg)
                    continue
            
            await browser.close()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"EXTRACTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Successfully extracted: {len(self.markers)} markers")
        if self.extraction_errors:
            logger.info(f"Errors: {len(self.extraction_errors)}")
        
        return self.markers
    
    async def _extract_markers_javascript(self, page) -> List[Dict[str, Any]]:
        """Extract all markers using JavaScript without clicking."""
        try:
            markers_data = await page.evaluate("""
                async () => {
                    const markers = [];
                    
                    // Get all marker elements
                    const markerElements = document.querySelectorAll('.leaflet-marker-icon');
                    console.log('Found ' + markerElements.length + ' marker elements');
                    
                    // Get all popup contents (popups are rendered but hidden)
                    const popups = document.querySelectorAll('.leaflet-popup-content');
                    
                    // Extract markers with their popup content
                    for (let i = 0; i < markerElements.length; i++) {
                        try {
                            const markerElem = markerElements[i];
                            const markerPane = markerElem.parentElement;
                            
                            // Find corresponding popup if it exists
                            let popupText = '';
                            let popupHtml = '';
                            
                            // Try to find popup in the DOM (they might already be rendered)
                            if (i < popups.length) {
                                popupText = popups[i].textContent || '';
                                popupHtml = popups[i].innerHTML || '';
                            }
                            
                            // If no popup text, try to extract from nearby elements
                            if (!popupText) {
                                const parent = markerElem.closest('.leaflet-pane');
                                if (parent) {
                                    const popupDiv = parent.parentElement.querySelector('.leaflet-popup-content');
                                    if (popupDiv) {
                                        popupText = popupDiv.textContent || '';
                                        popupHtml = popupDiv.innerHTML || '';
                                    }
                                }
                            }
                            
                            // Get marker position from style
                            const style = markerElem.getAttribute('style') || '';
                            const match = style.match(/translate3d\\((\\d+)px, (\\d+)px/);
                            const position = match ? {x: parseInt(match[1]), y: parseInt(match[2])} : {x: 0, y: 0};
                            
                            markers.push({
                                index: i,
                                popupText: popupText.trim(),
                                popupHtml: popupHtml,
                                position: position,
                                className: markerElem.className,
                            });
                        } catch(e) {
                            // Skip problematic markers
                        }
                    }
                    
                    return markers;
                }
            """)
            
            logger.info(f"Extracted basic marker data for {len(markers_data)} markers")
            
            # Now extract popup content more reliably by hovering/showing popups
            processed_markers = []
            
            for i, marker in enumerate(markers_data):
                try:
                    # Click marker to show popup
                    await page.locator('.leaflet-marker-icon').nth(i).click(force=True, timeout=2000)
                    await page.wait_for_timeout(300)
                    
                    # Get popup content
                    popup_content = await page.evaluate("""
                        () => {
                            const popup = document.querySelector('.leaflet-popup-content');
                            if (popup) {
                                return {
                                    text: popup.textContent,
                                    html: popup.innerHTML,
                                };
                            }
                            return null;
                        }
                    """)
                    
                    if popup_content:
                        text = popup_content['text'].strip()
                        parsed = self._parse_popup_text(text)
                        
                        processed_markers.append({
                            'id': f"dgt_{i}_{int(datetime.now().timestamp() * 1000)}",
                            'title': parsed.get('title', 'Unknown'),
                            'description': parsed.get('description', text),
                            'latitude': parsed.get('latitude', 0.0),
                            'longitude': parsed.get('longitude', 0.0),
                            'road_type': parsed.get('road_type'),
                            'cause': parsed.get('cause'),
                            'severity': parsed.get('severity'),
                            'full_text': text,
                        })
                    
                    # Close popup
                    await page.press('Escape')
                    await page.wait_for_timeout(100)
                    
                except Exception as e:
                    logger.debug(f"Error processing marker {i}: {e}")
                    # Add basic marker info even if popup extraction failed
                    processed_markers.append({
                        'id': f"dgt_{i}",
                        'title': f"Marker {i}",
                        'description': marker.get('popupText', ''),
                        'latitude': 0.0,
                        'longitude': 0.0,
                        'road_type': None,
                        'cause': None,
                        'severity': 'unknown',
                        'full_text': marker.get('popupText', ''),
                    })
            
            return processed_markers
            
        except Exception as e:
            logger.error(f"Error in JavaScript extraction: {e}")
            return []
    
    def _parse_popup_text(self, text: str) -> Dict[str, Any]:
        """Parse popup text to extract structured data."""
        parsed = {
            'title': '',
            'description': '',
            'latitude': 0.0,
            'longitude': 0.0,
            'road_type': None,
            'cause': None,
            'severity': None,
        }
        
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        if len(lines) > 0:
            parsed['title'] = lines[0][:100]
        
        # Look for specific patterns
        full_text = ' '.join(lines)
        
        # Extract cause
        cause_match = re.search(r'Causa[:\s]+([^A-Z\n]+)', full_text, re.IGNORECASE)
        if cause_match:
            parsed['cause'] = cause_match.group(1).strip()[:100]
        
        # Extract road info
        road_match = re.search(r'Carretera[:\s]*([A-Z]-?\d+)', full_text, re.IGNORECASE)
        if road_match:
            parsed['road_type'] = road_match.group(1)
        
        # Look for severity indicators
        if any(word in full_text.lower() for word in ['retención', 'denso', 'lento', 'congestion']):
            parsed['severity'] = 'high'
        elif any(word in full_text.lower() for word in ['circulación', 'marcha', 'normal']):
            parsed['severity'] = 'medium'
        else:
            parsed['severity'] = 'low'
        
        parsed['description'] = full_text[:500]
        
        return parsed
    
    def save_results(self, filename: str = 'dgt_markers_extracted.json'):
        """Save extracted markers to JSON file."""
        try:
            data = {
                'extraction_timestamp': datetime.now().isoformat(),
                'total_markers': len(self.markers),
                'markers': [marker.to_dict() for marker in self.markers],
                'errors': self.extraction_errors,
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n✓ Saved {len(self.markers)} markers to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return False
    
    def to_database_format(self) -> List[Dict[str, Any]]:
        """Convert markers to database insert format."""
        records = []
        
        for marker in self.markers:
            record = {
                'marker_id': marker.id,
                'location_name': marker.title,
                'description': marker.description,
                'latitude': marker.latitude,
                'longitude': marker.longitude,
                'road_type': marker.road_type,
                'cause': marker.cause,
                'severity': marker.severity,
                'data_type': 'incident',
                'timestamp': marker.extracted_at,
                'source': 'dgt_etraffic_web',
            }
            records.append(record)
        
        return records


async def main():
    """Main execution."""
    extractor = DGTMarkerExtractor()
    
    # Extract markers
    markers = await extractor.extract_all_markers()
    
    # Save results
    extractor.save_results()
    
    # Show database format
    db_records = extractor.to_database_format()
    
    logger.info(f"\n{'='*80}")
    logger.info("DATABASE FORMAT SAMPLE (first 3 markers):")
    logger.info(f"{'='*80}")
    
    for i, record in enumerate(db_records[:3]):
        logger.info(f"\nRecord {i+1}:")
        logger.info(json.dumps(record, indent=2, ensure_ascii=False))
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Ready to insert {len(db_records)} records into database")
    logger.info(f"{'='*80}")
    
    # Save database format
    with open('dgt_markers_db_format.json', 'w', encoding='utf-8') as f:
        json.dump(db_records, f, indent=2, ensure_ascii=False)
    logger.info("✓ Saved database format to dgt_markers_db_format.json")


if __name__ == "__main__":
    asyncio.run(main())
