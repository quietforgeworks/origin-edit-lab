// Read-only ABI observer for the pinned official LabPlot 2.12.1 binary.
// Mirrors public TextWrapper member order from the verified release header.
// Never modifies any argument, application object, imported data or styling.
#include <QString>
#include <QFile>
#include <QJsonObject>
#include <QJsonDocument>
#include <QTextDocument>
#include <QTextEdit>
#include <dlfcn.h>
struct ProbeTextWrapper { QString text; int mode; bool allowPlaceholder; QString textPlaceholder; };
static void logEntry(const QJsonObject& o) {
 if(qEnvironmentVariable("FONT_PROBE_OUT").isEmpty())return;
 QFile f(qEnvironmentVariable("FONT_PROBE_OUT"));if(f.open(QIODevice::WriteOnly|QIODevice::Append)){f.write(QJsonDocument(o).toJson(QJsonDocument::Compact));f.write("\n");}
}
extern "C" void _ZN9TextLabel7setTextERKNS_11TextWrapperE(void* self,const ProbeTextWrapper& v){
 auto real=(void(*)(void*,const ProbeTextWrapper&))dlsym(RTLD_NEXT,"_ZN9TextLabel7setTextERKNS_11TextWrapperE");
 auto get=(ProbeTextWrapper(*)(const void*))dlsym(RTLD_NEXT,"_ZNK9TextLabel4textEv");
 if(!real||!get){fprintf(stderr,"Probe: required method absent\n");abort();}
 const auto old=get(self);const QString incoming=v.text;real(self,v);const auto now=get(self);
 QTextDocument doc;doc.setHtml(incoming);
 if(!doc.toPlainText().isEmpty())logEntry({{"method","TextLabel::setText"},{"plain",doc.toPlainText()},{"before_html",old.text},{"incoming_html",incoming},{"after_html",now.text},{"mode",v.mode}});
}
extern "C" void _ZN9QTextEdit16setFontPointSizeEd(QTextEdit* self,double size){
 auto real=(void(*)(QTextEdit*,double))dlsym(RTLD_NEXT,"_ZN9QTextEdit16setFontPointSizeEd");
 if(!real){fprintf(stderr,"Probe: font method absent\n");abort();}
 real(self,size);
 logEntry({{"method","QTextEdit::setFontPointSize"},{"size",size},{"plain",self->toPlainText()},{"html",self->toHtml()}});
}
#include <QFont>
#include <QJsonArray>
#include <execinfo.h>
extern "C" void _ZN9QTextEdit14setCurrentFontERK5QFont(QTextEdit* self,const QFont& font){
 auto real=(void(*)(QTextEdit*,const QFont&))dlsym(RTLD_NEXT,"_ZN9QTextEdit14setCurrentFontERK5QFont");
 if(!real){fprintf(stderr,"Probe: current font method absent\n");abort();}
 const QString before=self->toHtml();const QString plain=self->toPlainText();real(self,font);
 QJsonArray stack;void* addresses[12];int count=backtrace(addresses,12);
 Dl_info caller{};dladdr(__builtin_return_address(0), &caller);
 QString callerObject=caller.dli_fname?QString::fromLocal8Bit(caller.dli_fname):QString();
 QString callerSymbol=caller.dli_sname?QString::fromLocal8Bit(caller.dli_sname):QString();
 QString callerOffset=QString::number(reinterpret_cast<quintptr>(__builtin_return_address(0))-reinterpret_cast<quintptr>(caller.dli_fbase),16);
 for(int i=1;i<count;i++){Dl_info info{};if(dladdr(addresses[i],&info)&&info.dli_sname)stack.append(QString::fromLatin1(info.dli_sname));}
 if(!plain.isEmpty())logEntry({{"method","QTextEdit::setCurrentFont"},{"plain",plain},{"requested_font",font.toString()},{"caller_object",callerObject},{"caller_symbol",callerSymbol},{"caller_object_offset_hex",callerOffset},{"before_html",before},{"after_html",self->toHtml()},{"stack",stack}});
}
