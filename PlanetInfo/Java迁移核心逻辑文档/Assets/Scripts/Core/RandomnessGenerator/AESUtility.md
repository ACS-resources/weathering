# AESUtility.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/RandomnessGenerator/AESUtility.cs`
- 命名空间：`Weathering`
- 代码行数：`78`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `class AESUtility`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public Encrypt(string str, string key)`
- `public Decrypt(string str, string key)`

### 3.2 属性签名

- `public AESUtility`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp


using System;

namespace Weathering
{
    //private void Test() {
    //    string source = AESPack.CorrectAnswer;
    //    string answerKey = "!!!!!!";
    //    string encrypted = AESUtility.Encrypt(source, answerKey);
    //    string decrypted = AESUtility.Decrypt(encrypted, answerKey);
    //    Debug.LogWarning($" {source} {encrypted} {decrypted}");
    //}
    public class AESUtility
    {
        ///// <summary>
        ///// 默认密钥-密钥的长度必须是32
        ///// </summary>
        //private const string PublicKey = "1234567890123456";
        ///// <summary>  
        ///// AES加密  
        ///// </summary>  
        ///// <param name="str">需要加密字符串</param>  
        ///// <returns>加密后字符串</returns>  
        //public static string Encrypt(string str) {
        //    return Encrypt(str, PublicKey);
        //}
        ///// <summary>  
        ///// AES解密  
        ///// </summary>  
        ///// <param name="str">需要解密字符串</param>  
        ///// <returns>解密后字符串</returns>  
        //public static string Decrypt(string str) {
        //    return Decrypt(str, PublicKey);
        //}

        /// <summary>
        /// 默认向量
        /// </summary>
        private const string Iv = "abcdefghijklmnop";
        /// <summary>
        /// AES加密
        /// </summary>
        /// <param name="str">需要加密的字符串</param>
        /// <param name="key">32位密钥</param>
        /// <returns>加密后的字符串</returns>
        public static string Encrypt(string str, string key) {
            byte[] keyArray = System.Text.Encoding.UTF8.GetBytes(key);
            byte[] toEncryptArray = System.Text.Encoding.UTF8.GetBytes(str);
            var rijndael = new System.Security.Cryptography.RijndaelManaged();
            rijndael.Key = keyArray;
            rijndael.Mode = System.Security.Cryptography.CipherMode.ECB;
            rijndael.Padding = System.Security.Cryptography.PaddingMode.PKCS7;
            rijndael.IV = System.Text.Encoding.UTF8.GetBytes(Iv);
            System.Security.Cryptography.ICryptoTransform cTransform = rijndael.CreateEncryptor();
            byte[] resultArray = cTransform.TransformFinalBlock(toEncryptArray, 0, toEncryptArray.Length);
            return Convert.ToBase64String(resultArray, 0, resultArray.Length);
        }
        /// <summary>
        /// AES解密
        /// </summary>
        /// <param name="str">需要解密的字符串</param>
        /// <param name="key">32位密钥</param>
        /// <returns>解密后的字符串</returns>
        public static string Decrypt(string str, string key) {
            byte[] keyArray = System.Text.Encoding.UTF8.GetBytes(key);
            byte[] toEncryptArray = Convert.FromBase64String(str);
            var rijndael = new System.Security.Cryptography.RijndaelManaged();
            rijndael.Key = keyArray;
            rijndael.Mode = System.Security.Cryptography.CipherMode.ECB;
            rijndael.Padding = System.Security.Cryptography.PaddingMode.PKCS7;
            rijndael.IV = System.Text.Encoding.UTF8.GetBytes(Iv);
            System.Security.Cryptography.ICryptoTransform cTransform = rijndael.CreateDecryptor();
            byte[] resultArray = cTransform.TransformFinalBlock(toEncryptArray, 0, toEncryptArray.Length);
            return System.Text.Encoding.UTF8.GetString(resultArray);
        }
    }
}
```

## 5. Java 迁移建议（本文件）

1. 先保留领域模型（类/接口）结构，再替换底层平台调用。
2. 若含 Unity API（如 `MonoBehaviour`、`Vector2Int`、`Tile`），先在 Java 中定义适配层接口与数据类。
3. 对外部可序列化字段保持字段语义与默认值一致，避免存档语义漂移。
4. 对反射型逻辑优先替换为“注册表 + 稳定 content_id”机制。
5. 将该文件纳入跨语言黄金样例测试，确保行为可回归。