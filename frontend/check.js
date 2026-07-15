const { execSync } = require('child_process');
try {
  const out = execSync('npx.cmd tsc --noEmit', { cwd: 'c:\\Users\\Charlie\\Downloads\\locwarp-main\\frontend', stdio: 'pipe' });
  console.log('SUCCESS:');
  console.log(out.toString());
} catch (e) {
  console.log('ERROR:');
  console.log(e.stdout ? e.stdout.toString() : e.message);
}
