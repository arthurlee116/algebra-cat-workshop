from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Food:
    food_id: str
    name: str
    description: str
    price: int
    image: str


FOODS: list[Food] = [
    Food("basic-kibble", "基础猫粮", "最普通的营养猫粮，适合日常补给", 5, "/images/basefood.PNG"),
    Food("premium-kibble", "优质猫粮", "额外添加维生素与鱼油，更香更脆", 10, "/images/base+1.PNG"),
    Food("small-fish", "小鱼干", "经典的小鱼干，嘎嘣脆", 15, "/images/base+2.PNG"),
    Food("big-fish", "大鱼", "整条鲜鱼烤得金黄冒油", 25, "/images/base+3.PNG"),
    Food("milk", "牛奶", "暖暖的一杯牛奶，帮助猫咪放松", 8, "/images/food-milk.png"),
    Food("canned", "猫罐头", "肉块丰富的高端罐头，香味四溢", 30, "/images/food-canned.png"),
    Food("feast", "豪华大餐", "牛排、鱼肉和蔬菜的盛宴，重大突破奖励", 50, "/images/food-feast.png"),
    Food("biscuit", "能量饼干", "甜甜的心形饼干，补充额外能量", 12, "/images/food-biscuit.png"),
]

FOOD_MAP = {food.food_id: food for food in FOODS}
