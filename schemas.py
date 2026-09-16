from pydantic import BaseModel, model_validator
from typing import Optional, Any

class ProductInfo(BaseModel):
    product_id: str
    title: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    condition: str
    brand: Optional[str] = None
    category: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    like_count: int = 0
    view_count: int = 0
    basket_count: int = 0
    shipment_status: str = ""
    seller_nickname: Optional[str] = None
    seller_score: Optional[float] = None
    seller_review_count: Optional[int] = None
    is_super_seller: bool = False

    @model_validator(mode='before')
    @classmethod
    def flatten_data(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        
        # Fix price formatting (e.g., "1.080" -> 1080.0)
        price_str = values.get("price", "0").replace(".", "").replace(",", ".")
        price = float(price_str)

        # Fix original price if it exists, otherwise leave as None
        orj_price_str = values.get("originalPrice")
        original_price = float(orj_price_str.replace(".", "").replace(",", ".")) if orj_price_str else None

        # Extract data from nested dictionaries
        brand = values.get("brand", {}).get("title") if values.get("brand") else None
        category = values.get("category", {}).get("title") if values.get("category") else None
        size = values.get("size", {}).get("title") if values.get("size") else None
        
        # Extract color (Comes as a list, get the first item)
        colours = values.get("colours", [])
        color = colours[0].get("title") if colours else None
        
        # Seller and Social Proof Information
        owner = values.get("owner", {})
        seller = owner.get("nickname")
        is_super = owner.get("isSuperSeller", False)
        score = owner.get("feedback", {}).get("feedbackAverage")
        review_count = owner.get("feedback", {}).get("feedbackCount")

        social = values.get("socialProof", {})
        views = social.get("viewCount", 0)

        # Return the flattened dictionary mapped to our model fields
        return {
            "product_id": str(values.get("id", "")),
            "title": values.get("title", ""),
            "description": values.get("description", ""),
            "price": price,
            "original_price": original_price,
            "condition": values.get("condition", ""),
            "brand": brand,
            "category": category,
            "size": size,
            "color": color,
            "like_count": values.get("likeCount", 0),
            "view_count": views,
            "basket_count": values.get("basketCount", 0),
            "shipment_status": values.get("shipmentTerm", ""),
            "seller_nickname": seller,
            "seller_score": score,
            "seller_review_count": review_count,
            "is_super_seller": is_super
        }