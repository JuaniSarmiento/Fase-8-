# 🎯 Quick Start Guide: AI Activity Wizard

## How to Use Your New AI-Powered Activity Creator

### 1️⃣ Open the Wizard
**Location**: Teacher Dashboard
**Action**: Click the **"Nueva Actividad"** button (top right)

### 2️⃣ Step 1: Configure Activity Details
Fill in the basic information:

```
📝 Título de la Actividad *
   Example: "Introducción a Python"

📚 Tema Principal *
   Example: "Variables y tipos de datos"

⚡ Dificultad *
   Choose: Fácil / Intermedio / Difícil
```

Click **"Siguiente"** when done.

### 3️⃣ Step 2: Provide Learning Material

**Option A: Upload PDF** 📄
- Click the "📄 Subir PDF" tab
- Click the file input
- Select your PDF file (max 10MB)
- See confirmation: ✅ filename.pdf (125.5 KB)

**Option B: Paste Text** ✍️
- Click the "✍️ Texto Manual" tab
- Paste your content into the large text area
- Can be course notes, documentation, examples, etc.

Click **"✨ Generar con IA"** to start!

### 4️⃣ Step 3: Watch the Magic ✨

Sit back and watch:
```
🔄 Spinner animating
━━━━━━━━━━━━━━━━━━━━━━  Progress bar filling
📊 42%                    Percentage updates
💬 "Diseñando ejercicios..." Message changes
```

Progress messages you'll see:
1. Analizando contexto...
2. Extrayendo conocimiento...
3. Diseñando ejercicios...
4. Generando casos de prueba...
5. Aplicando pedagogía...
6. Persistiendo datos...
7. ¡Casi listo!

### 5️⃣ Success! 🎉

When complete:
```
✅ Green checkmark appears
━━━━━━━━━━━━━━━━━━━━━━  100%
💚 "¡Actividad creada exitosamente!"
```

Toast notification pops up:
> **¡Actividad creada con éxito!**  
> "Introducción a Python" está lista para agregar ejercicios

Dialog closes automatically (1.5 seconds)  
**Your new activity appears in the table!** 🎯

## 🎬 Real-World Example

**Scenario**: Creating a Python fundamentals activity

**Step 1 Input**:
```
Title: "Python 101: Primeros Pasos"
Topic: "Variables, tipos de datos y operadores"
Difficulty: FACIL
```

**Step 2 - PDF Upload**:
```
File: python_basics_chapter1.pdf (2.3 MB)
✅ Successfully selected
```

**Step 3 - Processing**:
```
[0-15%]   🔄 Analizando contexto...
[15-30%]  🔄 Extrayendo conocimiento...
[30-50%]  🔄 Diseñando ejercicios...
[50-70%]  🔄 Generando casos de prueba...
[70-85%]  🔄 Aplicando pedagogía...
[85-95%]  🔄 Persistiendo datos...
[95-100%] 🔄 ¡Casi listo!
[100%]    ✅ ¡Actividad creada exitosamente!
```

**Result**:
New activity in dashboard:
- Title: Python 101: Primeros Pasos
- Status: 🟡 Borrador (Draft)
- Created: Just now

## 🚨 Error Handling

### Validation Errors
**If you forget a field in Step 1:**
```
🔴 Toast: "Por favor completa todos los campos"
```

**If you don't select a file (PDF mode):**
```
🔴 Toast: "Por favor selecciona un archivo PDF"
```

**If you don't paste text (Text mode):**
```
🔴 Toast: "Por favor ingresa el contenido del texto"
```

**If file is not PDF:**
```
🔴 Toast: "Solo se permiten archivos PDF"
```

**If file is too large (>10MB):**
```
🔴 Toast: "El archivo es demasiado grande (máx. 10MB)"
```

### API Errors
**If backend fails:**
```
🔴 Toast: "Error en la generación"
Description: [Backend error message]

Dialog returns to Step 2 (you can retry)
```

## 💡 Tips & Tricks

### Best Practices
1. **Use descriptive titles** - Help students understand what they'll learn
2. **Be specific in topic** - Better AI understanding = better exercises
3. **Match difficulty correctly** - Affects exercise complexity
4. **PDF works best** - Structured content gives best results
5. **Text is flexible** - Good for quick creation from notes

### File Requirements
- **Format**: PDF only
- **Size**: Maximum 10MB
- **Content**: Course materials, textbooks, lecture notes
- **Language**: Any (but specify language in metadata)

### Recommended PDFs
✅ Good:
- Course textbook chapters
- Lecture slides with code examples
- Tutorial documentation
- Programming guides

❌ Avoid:
- Scanned images without OCR
- Password-protected PDFs
- Corrupted files
- Pure image PDFs (no selectable text)

### Text Input Tips
- Include code examples
- Add explanations and context
- Structure with headings if possible
- Paste actual problems you want students to solve

## 🔄 What Happens Next?

After creation, you can:

1. **View the activity**: Click the activity name in table
2. **Edit metadata**: Use the edit dropdown
3. **Add exercises**: Generate or manually add
4. **Publish**: Change status to ACTIVE
5. **Share with students**: They can now see it

## 🎯 Success Indicators

You'll know it worked when:
- ✅ Toast notification appears
- ✅ Dialog closes automatically
- ✅ New row appears in activities table
- ✅ Status shows "Borrador"
- ✅ Timestamp shows "Just now" or recent time

## 🐛 Troubleshooting

**Dialog won't open?**
- Refresh the page
- Check browser console for errors
- Verify you're logged in as teacher

**Upload fails?**
- Check file size (<10MB)
- Verify file is actually .pdf
- Try a different PDF

**Stuck on processing?**
- Check browser console
- Verify backend is running
- Look at network tab for API errors

**Activity doesn't appear?**
- Wait 2-3 seconds for refresh
- Manually refresh page
- Check if it's in "Archivada" status

## 📱 Keyboard Shortcuts

- `Esc` - Close dialog (when not processing)
- `Tab` - Navigate between fields
- `Enter` - Submit form / next step (when ready)

---

## 🎉 You're Ready!

Click **"Nueva Actividad"** and start creating AI-powered learning experiences! 🚀

**Remember**: This is just the shell - you can still add exercises, customize instructions, and refine everything after creation. The AI gives you a great starting point!
