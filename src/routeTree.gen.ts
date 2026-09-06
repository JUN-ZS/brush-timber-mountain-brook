/* eslint-disable */
// @ts-nocheck
import { Route as rootRouteImport } from './routes/__root'
import { Route as IndexRouteImport } from './routes/index'
import { Route as DeployRouteImport } from './routes/deploy'
import { Route as MatrixRouteImport } from './routes/matrix'
import { Route as MissingRouteImport } from './routes/missing'
import { Route as RankRouteImport } from './routes/rank'
import { Route as BacktestRouteImport } from './routes/backtest'

const IndexRoute = IndexRouteImport.update({ id: '/', path: '/', getParentRoute: () => rootRouteImport } as any)
const DeployRoute = DeployRouteImport.update({ id: '/deploy', path: '/deploy', getParentRoute: () => rootRouteImport } as any)
const MatrixRoute = MatrixRouteImport.update({ id: '/matrix', path: '/matrix', getParentRoute: () => rootRouteImport } as any)
const MissingRoute = MissingRouteImport.update({ id: '/missing', path: '/missing', getParentRoute: () => rootRouteImport } as any)
const RankRoute = RankRouteImport.update({ id: '/rank', path: '/rank', getParentRoute: () => rootRouteImport } as any)
const BacktestRoute = BacktestRouteImport.update({ id: '/backtest', path: '/backtest', getParentRoute: () => rootRouteImport } as any)

export interface FileRoutesByFullPath { '/': typeof IndexRoute; '/deploy': typeof DeployRoute; '/matrix': typeof MatrixRoute; '/missing': typeof MissingRoute; '/rank': typeof RankRoute; '/backtest': typeof BacktestRoute }
export interface FileRoutesByTo { '/': typeof IndexRoute; '/deploy': typeof DeployRoute; '/matrix': typeof MatrixRoute; '/missing': typeof MissingRoute; '/rank': typeof RankRoute; '/backtest': typeof BacktestRoute }
export interface FileRoutesById { __root__: typeof rootRouteImport; '/': typeof IndexRoute; '/deploy': typeof DeployRoute; '/matrix': typeof MatrixRoute; '/missing': typeof MissingRoute; '/rank': typeof RankRoute; '/backtest': typeof BacktestRoute }
export interface FileRouteTypes { fileRoutesByFullPath: FileRoutesByFullPath; fullPaths: '/' | '/deploy' | '/matrix' | '/missing' | '/rank' | '/backtest'; fileRoutesByTo: FileRoutesByTo; to: '/' | '/deploy' | '/matrix' | '/missing' | '/rank' | '/backtest'; id: '__root__' | '/' | '/deploy' | '/matrix' | '/missing' | '/rank' | '/backtest'; fileRoutesById: FileRoutesById }
export interface RootRouteChildren { IndexRoute: typeof IndexRoute; DeployRoute: typeof DeployRoute; MatrixRoute: typeof MatrixRoute; MissingRoute: typeof MissingRoute; RankRoute: typeof RankRoute; BacktestRoute: typeof BacktestRoute }
declare module '@tanstack/react-router' { interface FileRoutesByPath { '/': { id: '/'; path: '/'; fullPath: '/'; preLoaderRoute: typeof IndexRouteImport; parentRoute: typeof rootRouteImport }; '/deploy': { id: '/deploy'; path: '/deploy'; fullPath: '/deploy'; preLoaderRoute: typeof DeployRouteImport; parentRoute: typeof rootRouteImport }; '/matrix': { id: '/matrix'; path: '/matrix'; fullPath: '/matrix'; preLoaderRoute: typeof MatrixRouteImport; parentRoute: typeof rootRouteImport }; '/missing': { id: '/missing'; path: '/missing'; fullPath: '/missing'; preLoaderRoute: typeof MissingRouteImport; parentRoute: typeof rootRouteImport }; '/rank': { id: '/rank'; path: '/rank'; fullPath: '/rank'; preLoaderRoute: typeof RankRouteImport; parentRoute: typeof rootRouteImport }; '/backtest': { id: '/backtest'; path: '/backtest'; fullPath: '/backtest'; preLoaderRoute: typeof BacktestRouteImport; parentRoute: typeof rootRouteImport } } }
const rootRouteChildren: RootRouteChildren = { IndexRoute, DeployRoute, MatrixRoute, MissingRoute, RankRoute, BacktestRoute }
export const routeTree = rootRouteImport._addFileChildren(rootRouteChildren)._addFileTypes<FileRouteTypes>()
import type { getRouter } from './router.tsx'
import type { createStart } from '@tanstack/react-start'
declare module '@tanstack/react-start' { interface Register { ssr: true; router: Awaited<ReturnType<typeof getRouter>> } }
