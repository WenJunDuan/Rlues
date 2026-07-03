// v9.1.8 PostToolUse: 格式化 (仅在工具已安装时执行)
const{execSync}=require('child_process');
const fs=require('fs');
const input=JSON.parse(fs.readFileSync('/dev/stdin','utf8'));
const f=input?.tool_input?.file_path||input?.tool_input?.path||'';
try{
  if(f.match(/\.(ts|tsx|js|jsx)$/)){
    // 仅当项目已安装 prettier 时格式化
    if(fs.existsSync('node_modules/.bin/prettier')){
      execSync(`npx prettier --write "${f}" 2>/dev/null`,{timeout:3000});
    }
  } else if(f.match(/\.py$/)){
    try{ execSync('python3 -c "import black" 2>/dev/null'); execSync(`python3 -m black "${f}" --quiet 2>/dev/null`,{timeout:3000}); }catch(e){}
  }
}catch(e){}
process.exit(0);
