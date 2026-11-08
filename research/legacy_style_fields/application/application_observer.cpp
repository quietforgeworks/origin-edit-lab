// Observe the unmodified official LabPlot application's Qt UI in offscreen mode.
// This helper contains no Origin parsing logic and does not change project data.
#include <QApplication>
#include <QWidget>
#include <QTimer>
#include <QLineEdit>
#include <QComboBox>
#include <QUrl>
#include <QPushButton>
#include <QTableView>
#include <QTreeView>
#include <signal.h>
#include <execinfo.h>
#include <unistd.h>
#include <QFile>
#include <QFileDialog>
#include <QDir>
#include <QTextStream>
#include <QPixmap>
#include <QAction>
#include <QDialog>
#include <QAbstractItemView>
#include <QAbstractItemModel>
#include <QMetaMethod>
#include <dlfcn.h>
#include <cstring>
#include <cstdint>
#include <cmath>
static int counter=0;
static void modelDump(QTextStream &s,QAbstractItemModel*m,QModelIndex p={},int depth=0){
 if(depth>6)return; int n=qMin(m->rowCount(p),20);
 for(int r=0;r<n;r++){s<<QString(depth*2,' ');for(int c=0;c<qMin(m->columnCount(p),20);c++)s<<m->data(m->index(r,c,p)).toString()<<" | ";s<<"\n";auto child=m->index(r,0,p);auto grand=m->index(0,0,child);if(grand.isValid() && grand.parent()==child)modelDump(s,m,child,depth+1);}
}
static void capture(){
 QString base=qEnvironmentVariable("OBSERVER_OUT")+QString("/%1").arg(++counter,3,10,QChar('0')); QFile f(base+"-widgets.txt");f.open(QIODevice::WriteOnly);QTextStream s(&f);s<<"Qt "<<qVersion()<<"\n";
 int k=0;for(auto*w:QApplication::topLevelWidgets())if(w->isVisible()){s<<"TOP "<<w->metaObject()->className()<<" "<<w->objectName()<<" "<<w->windowTitle()<<"\n";w->grab().save(base+QString("-window%1.png").arg(++k));}
 for(auto*w:QApplication::allWidgets()){if(!w->isVisible())continue;s<<w->metaObject()->className()<<" object="<<w->objectName()<<" text="<<w->property("text").toString()<<" enabled="<<w->isEnabled()<<" title="<<w->windowTitle()<<"\n";if(auto*v=qobject_cast<QAbstractItemView*>(w))if(v->model())modelDump(s,v->model());}
 for(auto*w:QApplication::allWidgets())if(auto*v=qobject_cast<QTableView*>(w))if(v->model()){s<<"ALL_TABLE visible="<<w->isVisible()<<" rows="<<v->model()->rowCount()<<" cols="<<v->model()->columnCount()<<"\n";modelDump(s,v->model());}
 for(auto*w:QApplication::topLevelWidgets()){for(auto*a:w->findChildren<QAction*>())s<<"ACTION "<<a->objectName()<<" | "<<a->text()<<" enabled="<<a->isEnabled()<<"\n";}
}
static QModelIndex findSheet(QAbstractItemModel*m,QModelIndex p={},int depth=0){if(depth>6)return {};for(int r=0;r<m->rowCount(p);r++){auto i=m->index(r,0,p);if((!qEnvironmentVariable("OBSERVER_SELECT_NAME").isEmpty() ? m->data(i).toString()==qEnvironmentVariable("OBSERVER_SELECT_NAME") : (m->data(m->index(r,1,p)).toString()=="Spreadsheet"&&m->data(i).toString()!="Spreadsheet")))return i;auto c=m->index(0,0,i);if(c.isValid()&&c.parent()==i){auto found=findSheet(m,i,depth+1);if(found.isValid())return found;}}return {};}
static void rawNumeric(){
 if(!qEnvironmentVariableIsSet("OBSERVER_RAW_NUMERIC"))return;
 QFile f(qEnvironmentVariable("OBSERVER_OUT")+"/native-app-values.tsv");f.open(QIODevice::WriteOnly);QTextStream s(&f);s<<"column\trow\thex_binary64\tdecimal17\tsignbit\n";
 int rows=-1,cols=-1;for(auto*w:QApplication::allWidgets())if(w->isVisible())if(auto*v=qobject_cast<QTableView*>(w))if(v->model()){rows=v->model()->rowCount();cols=v->model()->columnCount();}
 if(rows<0||cols<0){s<<"ERROR no imported table\n";return;}
 QFile display(qEnvironmentVariable("OBSERVER_OUT")+"/model-display-values.tsv");display.open(QIODevice::WriteOnly);QTextStream ds(&display);for(auto*w:QApplication::allWidgets())if(w->isVisible())if(auto*v=qobject_cast<QTableView*>(w))if(v->model()){for(int r=0;r<rows;r++){for(int c=0;c<cols;c++){if(c)ds<<"\t";ds<<v->model()->data(v->model()->index(r,c)).toString();}ds<<"\n";}}
 void*lib=dlopen(qEnvironmentVariable("OBSERVER_BUNDLED_LIB").toUtf8().constData(),RTLD_LAZY|RTLD_LOCAL);
 auto getcol=(const void*(*)(const void*,int))dlsym(lib?lib:RTLD_DEFAULT,"_ZNK11Spreadsheet6columnEi");
 auto getval=(double(*)(const void*,int))dlsym(lib?lib:RTLD_DEFAULT,"_ZNK6Column7valueAtEi");
 if(!getcol||!getval){s<<"ERROR missing public library functions\n";return;}
 for(auto*w:QApplication::allWidgets())if(w->isVisible())if(auto*v=qobject_cast<QTreeView*>(w))if(v->model()){auto idx=findSheet(v->model());if(idx.isValid()){
  const void*sheet=idx.internalPointer();for(int c=0;c<cols;c++){auto*col=getcol(sheet,c);if(!col){s<<"ERROR null column\n";return;}for(int r=0;r<rows;r++){double n=getval(col,r);uint64_t bits;memcpy(&bits,&n,8);s<<c<<"\t"<<r<<"\t"<<QString("%1").arg(bits,16,16,QChar('0'))<<"\t"<<QString::number(n,'g',17)<<"\t"<<std::signbit(n)<<"\n";}}return;
 }}
 s<<"ERROR no imported sheet model\n";
}
static QString activeSelection;
static void selectObject(const QString& name) {
 activeSelection.clear();
 qputenv("OBSERVER_SELECT_NAME", name.toUtf8());
 for(auto*w:QApplication::allWidgets())if(w->isVisible())if(auto*v=qobject_cast<QTreeView*>(w))if(v->model()) {
  auto idx=findSheet(v->model());
  if(idx.isValid()){v->setCurrentIndex(idx);QMetaObject::invokeMethod(v,"doubleClicked",Qt::DirectConnection,Q_ARG(QModelIndex,idx));activeSelection=name;return;}
 }
}
static void captureUnder(const QString& name,bool numeric=false){
 auto root=qEnvironmentVariable("OBSERVER_OUT");auto dir=root+"/"+name;QDir().mkpath(dir);
 if(name!="import-preview"&&name!="saved-application"&&name!=activeSelection){QFile skip(dir+"/NOT_SELECTED.txt");skip.open(QIODevice::WriteOnly);skip.write("Requested native object was not found; no claimed screenshot or values.\n");return;}
 qputenv("OBSERVER_OUT",dir.toUtf8());capture();if(numeric)rawNumeric();qputenv("OBSERVER_OUT",root.toUtf8());
}
static bool setup=false;
static void observe(){
 if(setup)return;setup=true;QApplication::setAttribute(Qt::AA_DontUseNativeDialogs);
 QTimer::singleShot(500,[]{
  for(auto*w:QApplication::topLevelWidgets())for(auto*a:w->findChildren<QAction*>())if(a->objectName()=="import_opj"){w->resize(1400,900);a->trigger();return;}
 });
 QTimer::singleShot(1500,[]{
  auto path=qEnvironmentVariable("OBSERVER_INPUT");fprintf(stderr,"OBSERVER_INPUT=%s\n",path.toUtf8().constData());
  for(auto*w:QApplication::allWidgets())if(w->isVisible()&&QString(w->metaObject()->className())=="KUrlComboBox"){
   if(auto*c=qobject_cast<QComboBox*>(w)){c->addItem(path);c->setCurrentIndex(c->count()-1);}
   QMetaObject::invokeMethod(w,"urlActivated",Qt::DirectConnection,Q_ARG(QUrl,QUrl::fromLocalFile(path)));
  }
 });
 QTimer::singleShot(2000,[]{
  if(qEnvironmentVariable("OBSERVER_LAYER_MODE")=="coordinate")for(auto*w:QApplication::allWidgets())if(auto*c=qobject_cast<QComboBox*>(w))if(c->objectName()=="cbGraphLayer"){c->setCurrentIndex(1);fprintf(stderr,"OBSERVER_LAYER_MODE coordinate, actual=%d\n",c->currentIndex());}
  captureUnder("import-preview");
 });
 QTimer::singleShot(2500,[]{
  for(auto*w:QApplication::topLevelWidgets())if(QString(w->metaObject()->className())=="ImportProjectDialog")
   for(auto*b:w->findChildren<QPushButton*>())if(b->isEnabled()&&b->text().remove("&")=="OK"){b->click();return;}
 });
 QTimer::singleShot(3500,[]{selectObject("Graph1");});
 QTimer::singleShot(4000,[]{captureUnder("Graph1");});
 QTimer::singleShot(4500,[]{selectObject("Graph2");});
 QTimer::singleShot(5000,[]{captureUnder("Graph2");});
 QTimer::singleShot(5500,[]{selectObject("Book1");});
 QTimer::singleShot(6000,[]{captureUnder("Book1",true);});
 QTimer::singleShot(6500,[]{selectObject("Book2");});
 QTimer::singleShot(7000,[]{captureUnder("Book2",true);});
 QTimer::singleShot(7500,[]{
  for(auto*w:QApplication::topLevelWidgets())if(QString(w->metaObject()->className())=="MainWin"){QMetaObject::invokeMethod(w,"saveProjectAs",Qt::DirectConnection);return;}
 });
 QTimer::singleShot(8500,[]{
  for(auto*w:QApplication::topLevelWidgets())if(auto*d=qobject_cast<QFileDialog*>(w)){
   auto path=qEnvironmentVariable("OBSERVER_OUT")+"/imported-application.lml";
   if(QFile::exists(path)){fprintf(stderr,"Refusing to overwrite %s\n",path.toUtf8().constData());return;}
   d->setDirectory(qEnvironmentVariable("OBSERVER_OUT"));d->selectFile("imported-application.lml");return;
  }
 });
 QTimer::singleShot(9000,[]{
  for(auto*w:QApplication::topLevelWidgets())if(auto*d=qobject_cast<QFileDialog*>(w)){
   if(auto*e=d->findChild<QLineEdit*>("fileNameEdit"))e->setText("imported-application.lml");
   QMetaObject::invokeMethod(d,"accept",Qt::DirectConnection);return;
  }
 });
 QTimer::singleShot(10000,[]{captureUnder("saved-application");});
}
extern "C" int _ZN12QApplication4execEv(){observe();auto real=(int(*)())dlsym(RTLD_NEXT,"_ZN12QApplication4execEv");return real();}
extern "C" int _ZN16QCoreApplication4execEv(){observe();auto real=(int(*)())dlsym(RTLD_NEXT,"_ZN16QCoreApplication4execEv");return real();}
extern "C" int _ZN7QDialog4execEv(QDialog*d){observe();auto real=(int(*)(QDialog*))dlsym(RTLD_NEXT,"_ZN7QDialog4execEv");return real(d);}

static void crash(int sig){void*b[48];int n=backtrace(b,48);backtrace_symbols_fd(b,n,2);_exit(128+sig);}
__attribute__((constructor)) static void registerCrash(){signal(SIGSEGV,crash);signal(SIGABRT,crash);}
