# 后端开发规范

## 技术栈
```yaml
运行时: Node.js 18+ / Python 3.10+
框架: Express / Fastify / FastAPI / NestJS
语言: TypeScript (Node) / Python (Type Hints)
数据库: PostgreSQL / MongoDB
ORM: Prisma / TypeORM / SQLAlchemy
测试: Jest / Pytest
```

## 项目结构 (Node.js)
```
src/
├── controllers/     # 请求处理
├── services/        # 业务逻辑
├── repositories/    # 数据访问
├── models/          # 数据模型
├── middlewares/     # 中间件
├── utils/           # 工具函数
├── types/           # 类型定义
├── config/          # 配置
└── tests/           # 测试
```

## API 设计

### RESTful 原则
```yaml
GET /users          # 列表
GET /users/:id      # 详情
POST /users         # 创建
PUT /users/:id      # 全量更新
PATCH /users/:id    # 部分更新
DELETE /users/:id   # 删除
```

### 响应格式
```typescript
// 成功响应
{
  "success": true,
  "data": { ... },
  "meta": { "page": 1, "total": 100 }
}

// 错误响应
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found"
  }
}
```

### HTTP 状态码
```yaml
200: 成功
201: 创建成功
204: 删除成功
400: 请求错误
401: 未认证
403: 无权限
404: 未找到
500: 服务器错误
```

## 分层架构

### Controller
```typescript
// 只处理 HTTP 相关
@Controller('users')
export class UserController {
  constructor(private userService: UserService) {}
  
  @Get(':id')
  async getUser(@Param('id') id: string) {
    return this.userService.findById(id);
  }
}
```

### Service
```typescript
// 业务逻辑
@Injectable()
export class UserService {
  constructor(private userRepo: UserRepository) {}
  
  async findById(id: string): Promise<User> {
    const user = await this.userRepo.findById(id);
    if (!user) throw new NotFoundException();
    return user;
  }
}
```

### Repository
```typescript
// 数据访问
@Injectable()
export class UserRepository {
  constructor(private prisma: PrismaService) {}
  
  async findById(id: string): Promise<User | null> {
    return this.prisma.user.findUnique({ where: { id } });
  }
}
```

## 错误处理

### 自定义错误
```typescript
class AppError extends Error {
  constructor(
    public code: string,
    public message: string,
    public statusCode: number = 400
  ) {
    super(message);
  }
}

// 使用
throw new AppError('USER_NOT_FOUND', 'User not found', 404);
```

### 全局错误处理
```typescript
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      success: false,
      error: { code: err.code, message: err.message }
    });
  }
  
  // 未知错误
  console.error(err);
  res.status(500).json({
    success: false,
    error: { code: 'INTERNAL_ERROR', message: 'Internal server error' }
  });
});
```

## 数据验证

### Zod (推荐)
```typescript
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(50),
  age: z.number().int().positive().optional()
});

type CreateUserInput = z.infer<typeof CreateUserSchema>;
```

### class-validator
```typescript
class CreateUserDto {
  @IsEmail()
  email: string;
  
  @IsString()
  @MinLength(2)
  name: string;
}
```

## 安全规范

### 认证
```yaml
方案: JWT + Refresh Token
存储: httpOnly Cookie (推荐) 或 Authorization Header
过期: Access 15min, Refresh 7days
```

### 安全清单
```yaml
- [ ] 输入验证
- [ ] SQL 注入防护 (使用 ORM)
- [ ] XSS 防护
- [ ] CSRF 防护
- [ ] Rate Limiting
- [ ] CORS 配置
- [ ] 敏感数据加密
- [ ] 日志脱敏
```

## 测试规范

### 单元测试
```typescript
describe('UserService', () => {
  let service: UserService;
  let mockRepo: jest.Mocked<UserRepository>;
  
  beforeEach(() => {
    mockRepo = { findById: jest.fn() };
    service = new UserService(mockRepo);
  });
  
  it('should return user by id', async () => {
    mockRepo.findById.mockResolvedValue({ id: '1', name: 'Test' });
    const user = await service.findById('1');
    expect(user.name).toBe('Test');
  });
});
```

### 集成测试
```typescript
describe('POST /users', () => {
  it('should create user', async () => {
    const res = await request(app)
      .post('/users')
      .send({ email: 'test@example.com', name: 'Test' });
    
    expect(res.status).toBe(201);
    expect(res.body.data.email).toBe('test@example.com');
  });
});
```

## 日志规范

### 结构化日志
```typescript
logger.info('User created', {
  userId: user.id,
  email: user.email,
  action: 'CREATE_USER'
});
```

### 日志级别
```yaml
error: 错误，需要处理
warn: 警告，需要关注
info: 重要业务事件
debug: 调试信息
```

## 检查清单
```markdown
- [ ] 分层清晰 (Controller/Service/Repository)
- [ ] 输入验证完整
- [ ] 错误处理统一
- [ ] 日志规范
- [ ] 测试覆盖核心逻辑
- [ ] 安全检查通过
```
