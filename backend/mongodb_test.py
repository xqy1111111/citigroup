from pymongo import MongoClient
import datetime

def test_mongodb_connection():
    try:
        # 连接到MongoDB（默认localhost和27017端口）
        client = MongoClient('mongodb://localhost:27017/')
        
        # 选择数据库和集合
        db = client['test_database']
        collection = db['test_collection']
        
        # 1. 插入操作（Create）
        test_document = {
            "name": "测试用户",
            "age": 25,
            "created_at": datetime.datetime.now()
        }
        insert_result = collection.insert_one(test_document)
        print(f"插入文档成功，ID: {insert_result.inserted_id}")
        
        # 2. 查询操作（Read）
        found_document = collection.find_one({"name": "测试用户"})
        print(f"查询结果: {found_document}")
        
        # 3. 更新操作（Update）
        update_result = collection.update_one(
            {"name": "测试用户"},
            {"$set": {"age": 26}}
        )
        print(f"更新文档数量: {update_result.modified_count}")
        
        # 4. 删除操作（Delete）
        delete_result = collection.delete_one({"name": "测试用户"})
        print(f"删除文档数量: {delete_result.deleted_count}")
        
        print("MongoDB 连接测试成功！所有操作均正常完成。")
        
    except Exception as e:
        print(f"MongoDB 连接或操作失败：{str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    test_mongodb_connection()