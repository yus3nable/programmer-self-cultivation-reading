# 全书目录

点击章名直接进入正文；展开后可选择小节。

## 书前资料

### [作者访谈录](front/访谈/sections/introduction.md)

### [序言一](front/序言一/sections/introduction.md)

### [序言二](front/序言二/sections/introduction.md)

### [序言三](front/序言三/sections/introduction.md)

### [导读](front/导读/sections/introduction.md)

## 第一部分 · 简介

### [第 1 章 温故而知新](chapters/01/sections/1.1.md)

- [1.1 从Hello World说起](chapters/01/sections/1.1.md)

- [1.2 万变不离其宗](chapters/01/sections/1.2.md)

- [1.3 站得高，望得远](chapters/01/sections/1.3.md)

- [1.4 操作系统做什么](chapters/01/sections/1.4.md)

- [1.5 内存不够怎么办](chapters/01/sections/1.5.md)

- [1.6 众人拾柴火焰高](chapters/01/sections/1.6.md)

- [1.7 本章小结](chapters/01/sections/1.7.md)

## 第二部分 · 静态链接

### [第 2 章 编译和链接](chapters/02/sections/2.1.md)

- [2.1 被隐藏了的过程](chapters/02/sections/2.1.md)

- [2.2 编译器做了什么](chapters/02/sections/2.2.md)

- [2.3 链接器年龄比编译器长](chapters/02/sections/2.3.md)

- [2.4 模块拼装——静态链接](chapters/02/sections/2.4.md)

- [2.5 本章小结](chapters/02/sections/2.5.md)

### [第 3 章 目标文件里有什么](chapters/03/sections/3.1.md)

- [3.1 目标文件的格式](chapters/03/sections/3.1.md)

- [3.2 目标文件是什么样的](chapters/03/sections/3.2.md)

- [3.3 挖掘 SimpleSection.o](chapters/03/sections/3.3.md)

- [3.4 ELF 文件结构描述](chapters/03/sections/3.4.md)

- [3.5 链接的接口——符号](chapters/03/sections/3.5.md)

- [3.6 调试信息](chapters/03/sections/3.6.md)

- [3.7 本章小结](chapters/03/sections/3.7.md)

### [第 4 章 静态链接](chapters/04/sections/4.1.md)

- [4.1 空间与地址分配](chapters/04/sections/4.1.md)

- [4.2 符号解析与重定位](chapters/04/sections/4.2.md)

- [4.3 COMMON 块](chapters/04/sections/4.3.md)

- [4.4 C++相关问题](chapters/04/sections/4.4.md)

- [4.5 静态库链接](chapters/04/sections/4.5.md)

- [4.6 链接过程控制](chapters/04/sections/4.6.md)

- [4.7 BFD 库](chapters/04/sections/4.7.md)

- [4.8 本章小结](chapters/04/sections/4.8.md)

### [第 5 章 Windows PE/COFF](chapters/05/sections/5.1.md)

- [5.1 Windows 的二进制文件格式 PE/COFF](chapters/05/sections/5.1.md)

- [5.2 PE 的前身——COFF](chapters/05/sections/5.2.md)

- [5.3 链接指示信息](chapters/05/sections/5.3.md)

- [5.4 调试信息](chapters/05/sections/5.4.md)

- [5.5 大家都有符号表](chapters/05/sections/5.5.md)

- [5.6 Windows 下的 ELF——PE](chapters/05/sections/5.6.md)

- [5.7 本章小结](chapters/05/sections/5.7.md)

## 第三部分 · 装载与动态链接

### [第 6 章 可执行文件的装载与进程](chapters/06/sections/6.1.md)

- [6.1 进程虚拟地址空间](chapters/06/sections/6.1.md)

- [6.2 装载的方式](chapters/06/sections/6.2.md)

- [6.3 从操作系统角度看可执行文件的装载](chapters/06/sections/6.3.md)

- [6.4 进程虚存空间分布](chapters/06/sections/6.4.md)

- [6.5 Linux 内核装载 ELF 过程简介](chapters/06/sections/6.5.md)

- [6.6 Windows PE 的装载](chapters/06/sections/6.6.md)

- [6.7 本章小结](chapters/06/sections/6.7.md)

### [第 7 章 动态链接](chapters/07/sections/7.1.md)

- [7.1 为什么要动态链接](chapters/07/sections/7.1.md)

- [7.2 简单的动态链接例子](chapters/07/sections/7.2.md)

- [7.3 地址无关代码](chapters/07/sections/7.3.md)

- [7.4 延迟绑定（PLT）](chapters/07/sections/7.4.md)

- [7.5 动态链接相关结构](chapters/07/sections/7.5.md)

- [7.6 动态链接的步骤和实现](chapters/07/sections/7.6.md)

- [7.7 显式运行时链接](chapters/07/sections/7.7.md)

- [7.8 本章小结](chapters/07/sections/7.8.md)

### [第 8 章 Linux 共享库的组织](chapters/08/sections/8.1.md)

- [8.1 共享库版本](chapters/08/sections/8.1.md)

- [8.2 符号版本](chapters/08/sections/8.2.md)

- [8.3 共享库系统路径](chapters/08/sections/8.3.md)

- [8.4 共享库查找过程](chapters/08/sections/8.4.md)

- [8.5 环境变量](chapters/08/sections/8.5.md)

- [8.6 共享库的创建和安装](chapters/08/sections/8.6.md)

- [8.7 本章小结](chapters/08/sections/8.7.md)

### [第 9 章 Windows 下的动态链接](chapters/09/sections/9.1.md)

- [9.1 DLL 简介](chapters/09/sections/9.1.md)

- [9.2 符号导出导入表](chapters/09/sections/9.2.md)

- [9.3 DLL 优化](chapters/09/sections/9.3.md)

- [9.4 C++ 与动态链接](chapters/09/sections/9.4.md)

- [9.5 DLL HELL](chapters/09/sections/9.5.md)

- [9.6 本章小结](chapters/09/sections/9.6.md)

## 第四部分 · 库与运行库

### [库与运行库：导言](front/第四部分导言/sections/introduction.md)

### [第 10 章 内存](chapters/10/sections/10.1.md)

- [10.1 程序的内存布局](chapters/10/sections/10.1.md)

- [10.2 栈与调用惯例](chapters/10/sections/10.2.md)

- [10.3 堆与内存管理](chapters/10/sections/10.3.md)

- [10.4 本章小结](chapters/10/sections/10.4.md)

### [第 11 章 运行库](chapters/11/sections/11.1.md)

- [11.1 入口函数和程序初始化](chapters/11/sections/11.1.md)

- [11.2 C/C++ 运行库](chapters/11/sections/11.2.md)

- [11.3 运行库与多线程](chapters/11/sections/11.3.md)

- [11.4 C++ 全局构造与析构](chapters/11/sections/11.4.md)

- [11.5 fread 实现](chapters/11/sections/11.5.md)

- [11.6 本章小结](chapters/11/sections/11.6.md)

### [第 12 章系统调用与 API](chapters/12/sections/12.1.md)

- [12.1 系统调用介绍](chapters/12/sections/12.1.md)

- [12.2 系统调用原理](chapters/12/sections/12.2.md)

- [12.3 Windows API](chapters/12/sections/12.3.md)

- [12.4 本章小结](chapters/12/sections/12.4.md)

### [第 13 章 运行库实现](chapters/13/sections/13.1.md)

- [13.1 C 语言运行库](chapters/13/sections/13.1.md)

- [13.2 如何使用 Mini CRT](chapters/13/sections/13.2.md)

- [13.3 C++ 运行库实现](chapters/13/sections/13.3.md)

- [13.4 如何使用 Mini CRT++](chapters/13/sections/13.4.md)

- [13.5 本章小结](chapters/13/sections/13.5.md)

## 附录与索引

### [附录 A](chapters/A/sections/A.1.md)

- [A.1 字节序（Byte Order）](chapters/A/sections/A.1.md)

- [A.2 ELF 常见段](chapters/A/sections/A.2.md)

- [A.3 常用开发工具命令行参考](chapters/A/sections/A.3.md)

### [索引](front/索引/sections/introduction.md)
