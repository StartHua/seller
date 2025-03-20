class RecommendationAgent:
    """推荐系统Agent，为不同用户生成个性化推荐"""
    
    def __init__(self, llm_service, database):
        self.llm = llm_service
        self.db = database
        
    def generate_recommendations(self, user_profile, user_history):
        """生成个性化推荐"""
        # 从数据库获取商品
        session = self.db.Session()
        products = session.query(self.db.Product).all()
        
        # 使用LLM分析用户喜好并匹配最合适的商品
        recommendations = self.llm.personalized_recommendations(
            user_profile,
            user_history,
            products
        )
        return recommendations
    
    def explain_recommendation(self, recommendation_id):
        """提供推荐解释"""
        explanation = self.llm.generate_recommendation_explanation(recommendation_id)
        return explanation 