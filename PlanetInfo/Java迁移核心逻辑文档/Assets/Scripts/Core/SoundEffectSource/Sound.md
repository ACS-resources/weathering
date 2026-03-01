# Sound.cs（Java 迁移解构文档）

- 源文件：`Assets/Scripts/Core/SoundEffectSource/Sound.cs`
- 命名空间：`Weathering`
- 代码行数：`200`

## 1. 文件定位与迁移价值

该文件属于 Weathering 核心逻辑范围。迁移到 Java 时，应优先保持其**状态模型、行为约束、输入输出契约、序列化语义**一致。

## 2. 类型清单（逐项映射）

- `interface ISound`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class SoundEnabled`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class MusicEnabled`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class SoundVolume`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class MusicVolume`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class WeatherEnabled`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class WeatherVolume`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class SoundMusicIndex`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。
- `class Sound`：建议在 Java 中映射为同名（或语义等价）类型，并保留可见性与职责边界。

## 3. 函数/属性接口梳理

### 3.1 方法签名

- `public Get(string sound)`
- `public Play(AudioClip sound)`
- `public Play(string sound)`
- `private Awake()`
- `private Start()`
- `public PlayDefaultSound()`
- `private HashMusicIndex()`
- `private Update()`

### 3.2 属性签名

- `public ISound`
- `public SoundEnabled`
- `public MusicEnabled`
- `public SoundVolume`
- `public MusicVolume`
- `public WeatherEnabled`
- `public WeatherVolume`
- `public SoundMusicIndex`
- `public Ins`
- `public SoundVolume`
- `public WeatherEnabled`
- `public WeatherVolume`
- `public RainDensity`
- `public MusicEnabled`
- `public MusicVolume`

## 4. 实现机制详解（按源码解读）

> 本节直接嵌入源码，便于逐行建立 Java 对照实现与 prototype test。

```csharp

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Weathering
{
    public interface ISound
    {



        string PlayingMusicName { get; }
        bool IsPlaying { get; }




        AudioClip Get(string sound);
        void PlayDefaultSound();
        void Play(string sound);
        void Play(AudioClip sound);
        float SoundVolume { get; set; }


        float RainDensity { set; }
        bool WeatherEnabled { get; set; }
        float WeatherVolume { get; set; }


        int MusicCount { get; }
        bool MusicEnabled { get; set; }
        float MusicVolume { get; set; }
    }

    public class SoundEnabled { }
    public class MusicEnabled { }
    public class SoundVolume { }
    public class MusicVolume { }
    public class WeatherEnabled { }
    public class WeatherVolume { }

    public class SoundMusicIndex { }

    public class Sound : MonoBehaviour, ISound
    {
        public static ISound Ins { get; private set; }

        public bool IsPlaying => musicSource.isPlaying;


        [SerializeField]
        private AudioSource sfxSource;
        [SerializeField]
        private AudioSource musicSource;
        [SerializeField]
        private AudioSource weatherSource;

        [SerializeField]
        private AudioClip defaultSound;

        [SerializeField]
        private AudioClip[] defaultMusics;

        public int MusicCount => defaultMusics.Length;

        [SerializeField]
        private AudioClip[] Sounds;




        public AudioClip Get(string sound) {
            AudioClip audioClip;
            if (!dict.TryGetValue(sound, out audioClip)) {
                throw new Exception(sound);
            }
            return audioClip;
        }

        public void Play(AudioClip sound) {
            if (Globals.Ins.Bool<SoundEnabled>()) {
                sfxSource.PlayOneShot(sound);
            }
        }
        public void Play(string sound) {
            Play(Get(sound));
        }


        private readonly Dictionary<string, AudioClip> dict = new Dictionary<string, AudioClip>();
        private void Awake() {
            if (Ins != null) throw new Exception();
            Ins = this;

            foreach (var sound in Sounds) {
                if (sound == null) {
                    continue;
                }
                dict.Add(sound.name, sound);
            }

            // musicIndex = Math.Abs((int)HashUtility.Hash((uint)TimeUtility.GetTicks())) % defaultMusics.Length;
        }
        // private IValue musicIndex;
        private void Start() {
            // musicIndex = Globals.Ins.Values.GetOrCreate<SoundMusicIndex>();
        }


        private const string defaultSoundName = "mixkit-cool-interface-click-tone-2568";
        public void PlayDefaultSound() {
            if (!Globals.Ins.Bool<SoundEnabled>()) {
                return;
            }
            if (defaultSound == null) defaultSound = Get(defaultSoundName);
            sfxSource.PlayOneShot(defaultSound);
        }

        public float SoundVolume { get => sfxSource.volume; set => sfxSource.volume = value; }




        public bool WeatherEnabled { get => weatherSource.isPlaying; set {
                // if (value) weatherSource.Play(); else weatherSource.Stop(); 
                if (value && !weatherSource.isPlaying) {
                    weatherSource.Play();
                } else if (!value && weatherSource.isPlaying) {
                    weatherSource.Stop();
                }
            }
        }

        private float weatherVolume = 0;
        public float WeatherVolume { get => weatherSource.volume; set {
                weatherVolume = value;
            } 
        }

        public float RainDensity { set {
                weatherSource.volume = value * weatherVolume;
            } 
        }


        /// <summary>
        /// music
        /// </summary>
        public string PlayingMusicName => musicSource.clip.name;
        public bool MusicEnabled {
            get => musicSource.isPlaying; set {
                if (value) {
                    if (musicSource.clip != null && musicSource.isPlaying) {
                        return;
                    }
                    musicSource.clip = defaultMusics[HashMusicIndex()];
                    musicSource.Play();
                } else {
                    musicSource.Stop();
                }
            }
        }
        private uint HashMusicIndex() {
            return (uint)(HashUtility.Hash((uint)(TimeUtility.GetSecondsInDouble() / 30)) % defaultMusics.Length);
        }

        public float MusicVolume { get => musicSource.volume; set => musicSource.volume = value; }


        /// <summary>
        /// auto pause
        /// </summary>

        private uint lastMusicIndex = 0;

        private const float silencedTime = 60f;
        private float timeSilencedAcc = 0;
        private void Update() {
            if (!musicSource.isPlaying) {
                timeSilencedAcc += Time.deltaTime;

                uint thisMusicIndex = HashMusicIndex();
                if (timeSilencedAcc > silencedTime && Globals.Ins.Bool<MusicEnabled>() && thisMusicIndex != lastMusicIndex) {
                    timeSilencedAcc = 0;
                    MusicEnabled = true;
                }
                lastMusicIndex = thisMusicIndex;
            }
            //else {
            //    float time = musicSource.time;
            //    if (time < fadeInTime + 1) {
            //        float maxVolume = MusicVolume;
            //        musicSource.volume = Mathf.Lerp(0, maxVolume, time / fadeInTime);
            //    }
            //}
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